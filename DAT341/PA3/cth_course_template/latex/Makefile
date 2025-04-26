
TARGET=template

$(TARGET).pdf: $(TARGET).tex $(TARGET).bib
	pdflatex $(TARGET).tex; bibtex $(TARGET); bibtex $(LR); pdflatex $(TARGET); pdflatex $(TARGET)

clean:
	rm -f $(TARGET).pdf *.log *.dvi *.aux *~ *.toc *.bbl *.blg *.bak *.out
