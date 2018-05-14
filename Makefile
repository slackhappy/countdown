ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
DEPS=$(ROOT_DIR)/.deps
PYTHON=$(ROOT_DIR)/.venv/bin/python
MATRIX_REPO=$(DEPS)/rpi-rgb-led-matrix
PROTO=$(DEPS)/protobuf-3.5.1
GTFS=$(ROOT_DIR)/gtfs_realtime_pb2.py
MATRIX_LIB=$(MATRIX_REPO)/bindings/python/rgbmatrix/graphics.so
all: $(MATRIX_LIB) $(GTFS)


$(MATRIX_LIB): $(PYTHON) $(MATRIX_REPO)
	make -C $(MATRIX_REPO) build-python
	make -C $(MATRIX_REPO) install-python PYTHON=$(PYTHON)

$(MATRIX_REPO): $(PYTHON)
	mkdir -p .deps
	cd .deps && git clone https://github.com/hzeller/rpi-rgb-led-matrix || echo exists

$(GTFS):
	curl -L  https://developers.google.com/transit/gtfs-realtime/gtfs-realtime.proto -o $(DEPS)/gtfs-realtime.proto
	protoc -I=$(DEPS) --python_out=. $(DEPS)/gtfs-realtime.proto 


$(PYTHON):
	virtualenv .venv --system-site-packages
	# sudo apt-get install libtiff5-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms1-dev libwebp-dev
	.venv/bin/pip install Pillow

clean:
	rm -rf .deps
	rm -rf .venv
