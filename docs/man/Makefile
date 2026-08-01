# FILES := $(shell echo docs/dot{,-{ln,rm,sync,manage,unmanage,adopt,orphan,list,edit,cat,mod,git}}.ronn.1)
# FILES := $(shell echo dot{,-ln}.ronn.1)
FILES := $(shell ls *.ronn | grep -v 'html')
RONN_STYLE=.

html:
	RONN_STYLE=$(RONN_STYLE) ronn --html $(FILES) --style=toc,extra
# 	Remove any weird un-sectioned renders
	rm -f *.ronn.html

man:
	ronn --roff $(FILES)

# index:
# 	uv run index.py