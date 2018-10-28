ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
DEPS=$(ROOT_DIR)/.deps
PYTHON=$(ROOT_DIR)/.venv/bin/python
FONT_NAME=6x12.bdf
FONT=$(ROOT_DIR)/$(FONT_NAME)
MATRIX_REPO=$(DEPS)/rpi-rgb-led-matrix
MATRIX_LIB=$(MATRIX_REPO)/bindings/python/rgbmatrix/graphics.so
all: $(MATRIX_LIB) $(FONT)


$(MATRIX_LIB): $(PYTHON) $(MATRIX_REPO)
	make -C $(MATRIX_REPO) build-python
	make -C $(MATRIX_REPO) install-python PYTHON=$(PYTHON)

$(FONT): $(MATRIX_REPO)
	cp $(MATRIX_REPO)/fonts/$(FONT_NAME) $(ROOT_DIR)/

$(MATRIX_REPO): $(PYTHON)
	mkdir -p .deps
	cd .deps && git clone https://github.com/hzeller/rpi-rgb-led-matrix || echo exists

$(PYTHON):
	virtualenv .venv --system-site-packages
	# sudo apt-get install libtiff5-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms1-dev libwebp-dev
	.venv/bin/pip install Pillow

run:
	cd $(ROOT_DIR)
	sudo $(PYTHON) countdown.py --glyphs 10x12_sub.bdf --font $(FONT_NAME)

clean:
	rm -rf .deps
	rm -rf .venv
