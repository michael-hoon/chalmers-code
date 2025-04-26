import os
import argparse
import sys
import time
import multiprocessing as mp

def get_filenames(path):
    """
    A generator function: Iterates through all .txt files in the path and
    returns the full names of the files

    Parameters:
    - path : string, path to walk through

    Yields:
    The full filenames of all files ending in .txt
    """
    for (root, dirs, files) in os.walk(path):
        for file in files:
            if file.endswith('.txt'):
                yield f'{root}/{file}'

def get_file(path):
    """
    Reads the content of the file and returns it as a string.

    Parameters:
    - path : string, path to a file

    Return value:
    The content of the file in a string.
    """
    with open(path,'r') as f:
        return f.read()

def count_words_in_file(filename_queue,wordcount_queue,batch_size):
    """
    Counts the number of occurrences of words in the file
    Performs counting until a None is encountered in the queue
    Counts are stored in wordcount_queue
    Whitespace is ignored

    Parameters:
    - filename_queue, multiprocessing queue :  will contain filenames and None as a sentinel to indicate end of input
    - wordcount_queue, multiprocessing queue : (word,count) dictionaries are put in the queue, and end of input is indicated with a None
    - batch_size, int : size of batches to process

    Returns: None
    """
    while True:
        filename = filename_queue.get()
        if filename is None:
            wordcount_queue.put(None)
            break
        content = get_file(filename)
        counts = dict()
        # batch processing
        for i in range(0, len(content.split()), batch_size):
            batch = content.split()[i:i + batch_size]
            for word in batch:
                if word in counts:
                    counts[word] += 1
                else:
                    counts[word] = 1
        wordcount_queue.put(counts)
        # end of input
        wordcount_queue.put(None)
        break
    return None



def get_top10(counts):
    """
    Determines the 10 words with the most occurrences.
    Ties can be solved arbitrarily.

    Parameters:
    - counts, dictionary : a mapping from words (str) to counts (int)
    
    Return value:
    A list of (count,word) pairs (int,str)
    """
    sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    
    top_10 = sorted_counts[:10]
    
    top_10_pairs = [(count, word) for word, count in top_10]
    
    return top_10_pairs



def merge_counts(out_queue,wordcount_queue,num_workers):
    """
    Merges the counts from the queue into the shared dict global_counts. 
    Quits when num_workers Nones have been encountered.

    Parameters:
    - global_counts, manager dict : global dictionary where to store the counts
    - wordcount_queue, manager queue : queue that contains (word,count) pairs and Nones to signal end of input from a worker
    - num_workers, int : number of workers (i.e., how many Nones to expect)

    Return value: None
    """
    global_counts = dict()
    completed_workers = 0
    while completed_workers < num_workers:
        counts = wordcount_queue.get()
        if counts is None:
            completed_workers += 1
        else:
            for word, count in counts.items():
                global_counts[word] = global_counts.get(word, 0) + count
    
    checksum = compute_checksum(global_counts)
    top_10 = get_top10(global_counts)
    out_queue.put((checksum, top_10))
    return None



def compute_checksum(counts):
    """
    Computes the checksum for the counts as follows:
    The checksum is the sum of products of the length of the word and its count

    Parameters:
    - counts, dictionary : word to count dictionary

    Return value:
    The checksum (int)
    """
    checksum = 0
    for word, count in counts.items():
        checksum += len(word) * count
    return checksum


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Counts words of all the text files in the given directory')
    parser.add_argument('-w', '--num-workers', help = 'Number of workers', default=1, type=int)
    parser.add_argument('-b', '--batch-size', help = 'Batch size', default=1, type=int)
    parser.add_argument('path', help = 'Path that contains text files')
    args = parser.parse_args()

    path = args.path

    if not os.path.isdir(path):
        sys.stderr.write(f'{sys.argv[0]}: ERROR: `{path}\' is not a valid directory!\n')
        quit(1)

    num_workers = args.num_workers
    if num_workers < 1:
        sys.stderr.write(f'{sys.argv[0]}: ERROR: Number of workers must be positive (got {num_workers})!\n')
        quit(1)

    batch_size = args.batch_size
    if batch_size < 1:
        sys.stderr.write(f'{sys.argv[0]}: ERROR: Batch size must be positive (got {batch_size})!\n')
        quit(1)

    # construct workers and queues
    manager = mp.Manager()
    filename_queue = manager.Queue()
    wordcount_queue = manager.Queue()
    out_queue = manager.Queue()

    # worker processes
    workers = []
    for i in range(num_workers):
        worker = mp.Process(target=count_words_in_file, args=(filename_queue, wordcount_queue, batch_size))
        worker.start()
        workers.append(worker)

    # construct a special merger process
    merger = mp.Process(target=merge_counts, args=(out_queue, wordcount_queue, num_workers))
    merger.start()

    # put filenames into the input queue
    for filename in get_filenames(path):
        filename_queue.put(filename)

    # put None in queue to signal end of input
    for i in range(num_workers):
        filename_queue.put(None)
    
    # wait for all workers to finish
    for worker in workers:
        worker.join()

    # workers then put dictionaries for the merger
    # the merger shall return the checksum and top 10 through the out queue
    checksum, top_10 = out_queue.get()
    merger.join()

    # print the checksum and top 10
    print(f'Checksum: {checksum}')
    print('Top 10 words:')
    for count, word in top_10:
        print(f'{word}: {count}')