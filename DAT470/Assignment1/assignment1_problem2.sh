#!/bin/bash

echo -e "==== System Information for $(hostname) ====\n"

get_cpu_info() {
	echo "==== CPU Information ===="
	lscpu | grep -E 'Model name|Socket|Core|Thread|MHz|Architecture|L[123] cache|L1d cache|L1i cache|Level'
	echo -e "Cache Line Length: $(getconf LEVEL1_DCACHE_LINESIZE) bytes\n"
}

get_memory_info() {
	echo "==== Memory Information ===="
	free -h | grep Mem
	echo ""
}

get_gpu_info() {
	echo "==== GPU Information ===="
	if command -v nvidia-smi &>/dev/null; then
		nvidia-smi --query-gpu=name,memory.total --format=csv
	else
		echo "No NVIDIA GPU Detected"
	fi
	echo ""
}

get_storage_info() {
	echo "==== Storage Information ===="
	df -hT /data | awk 'NR==1 || NR==2'
	echo ""
}

get_os_info() {
	echo "==== OS Information ===="
	uname -srmo
	lsb_release -d
	echo ""
}

get_python_info() {
	echo "==== Python Information ===="
	if command -v python3 &>/dev/null; then
		python3 --version
		readlink -f $(which python3)
	else
		echo "Python3 not found"
	fi
	echo ""
}

get_cpu_info
get_memory_info
get_gpu_info
get_storage_info
get_os_info
get_python_info
