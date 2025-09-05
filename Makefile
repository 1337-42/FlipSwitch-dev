# Kernel Module Makefile
# Clean and organized build system with debug and obfuscation support

# Project structure
SRC_DIR := src
SCRIPTS_DIR := scripts
BUILD_DIR := build

# Primary target object
obj-m += main.o

# Kernel build directory
KDIR := /lib/modules/$(shell uname -r)/build

# Build flags
ifdef DEBUG
    ccflags-y += -DDEBUG -I$(PWD)/$(SRC_DIR)
else
    ccflags-y += -Os -DNDEBUG -I$(PWD)/$(SRC_DIR)
endif

# Ensure build directory exists
$(shell mkdir -p $(BUILD_DIR))

# Default target: build without debug
all: clean
	@echo "Building kernel module (optimized, no debug)..."
	cp $(SRC_DIR)/main.c $(SRC_DIR)/main.h .
	make -C $(KDIR) M=$(PWD) modules
	@echo "Stripping debug information..."
	strip --strip-debug --strip-unneeded main.ko
	mv main.ko $(BUILD_DIR)/
	@rm -f main.c main.h
	@echo "Build complete: $(BUILD_DIR)/main.ko"

# Debug build
debug: clean
	@echo "Building kernel module with debug information..."
	cp $(SRC_DIR)/main.c $(SRC_DIR)/main.h .
	make DEBUG=1 -C $(KDIR) M=$(PWD) modules
	mv main.ko $(BUILD_DIR)/main_debug.ko
	@rm -f main.c main.h
	@echo "Debug build complete: $(BUILD_DIR)/main_debug.ko"

# Test without debug
test: all install
	@echo "Running test sequence on optimized module..."
	@$(MAKE) _run_test_sequence
	@$(MAKE) uninstall

# Test with debug
debug-test: debug install-debug
	@echo "Running test sequence on debug module..."
	@$(MAKE) _run_test_sequence
	@$(MAKE) uninstall-debug

# Full obfuscation: function + string obfuscation + metadata randomization
obfuscate: clean
	@echo "=== Full Obfuscation Process ==="
	@echo "Step 1: Randomizing module metadata..."
	python3 $(SCRIPTS_DIR)/randomize_metadata.py $(SRC_DIR)/main.h $(BUILD_DIR)/main_temp_header.h
	@echo "Step 2: Function/variable obfuscation..."
	python3 $(SCRIPTS_DIR)/func_obfuscate.py $(BUILD_DIR)/main_temp_header.h $(SRC_DIR)/main.c $(BUILD_DIR)/main_temp_obf.c $(BUILD_DIR)/main_temp_header.h
	@echo "Step 3: String obfuscation on function-obfuscated code..."
	python3 $(SCRIPTS_DIR)/obfuscate_and_replace.py $(BUILD_DIR)/main_temp_obf.c main_obf.c $(BUILD_DIR)/obfuscated_strings.h
	cp $(BUILD_DIR)/main_temp_header.h .
	cp $(BUILD_DIR)/obfuscated_strings.h .
	cp func_obf_macros.h $(BUILD_DIR)/
	@echo "Step 4: Building fully obfuscated kernel module..."
	make -C $(KDIR) M=$(PWD) EXTRA_CFLAGS="-include obfuscated_strings.h -include func_obf_macros.h -I$(PWD)/$(SRC_DIR)" obj-m+=main_obf.o modules
	@echo "Step 5: Stripping debug information..."
	strip --strip-debug --strip-unneeded main_obf.ko
	mv main_obf.ko $(BUILD_DIR)/
	@echo "Cleaning temporary files..."
	@rm -f main_obf.c main_temp_header.h obfuscated_strings.h func_obf_macros.h
	@echo "Full obfuscation complete: $(BUILD_DIR)/main_obf.ko"

# Test obfuscated module
obfuscate-test: obfuscate
	@echo "Running test sequence on fully obfuscated module..."
	sudo insmod $(BUILD_DIR)/main_obf.ko
	@$(MAKE) _run_test_sequence_obf
	sudo rmmod main_obf

# Internal test sequence helper (for regular module)
_run_test_sequence:
	@echo "Waiting for module initialization..."
	sleep 3
	@echo "Kernel messages after load:"
	sudo dmesg | tail -n 20
	@echo "Testing kill syscall hook (signal 64)..."
	kill -64 99999 || true
	@echo "Kernel messages after test:"
	sudo dmesg | tail -n 20
	@echo "Current user permissions:"
	id
	@echo "Test sequence complete."

# Internal test sequence helper (for obfuscated module)
_run_test_sequence_obf:
	@echo "Waiting for obfuscated module initialization..."
	sleep 3
	@echo "Kernel messages after obfuscated load:"
	sudo dmesg | tail -n 20
	@echo "Testing obfuscated kill syscall hook (signal 64)..."
	kill -64 99999 || true
	@echo "Kernel messages after obfuscated test:"
	sudo dmesg | tail -n 20
	@echo "Current user permissions:"
	id
	@echo "Obfuscated test sequence complete."

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	make -C $(KDIR) M=$(PWD) clean
	@rm -rf $(BUILD_DIR)/*
	@rm -f main.c main.h main_obf.c main_temp_header.h
	@rm -f obfuscated_strings.h func_obf_macros.h
	@rm -f *.ko *.o *.mod *.mod.c Module.symvers modules.order

# Install regular module
install:
	@echo "Installing kernel module..."
	sudo insmod $(BUILD_DIR)/main.ko

# Install debug module
install-debug:
	@echo "Installing debug kernel module..."
	sudo insmod $(BUILD_DIR)/main_debug.ko

# Install obfuscated module
install-obf:
	@echo "Installing obfuscated kernel module..."
	sudo insmod $(BUILD_DIR)/main_obf.ko

# Uninstall module
uninstall:
	@echo "Uninstalling kernel module..."
	sudo rmmod main || true

# Uninstall debug module
uninstall-debug:
	@echo "Uninstalling debug kernel module..."
	sudo rmmod main || true

# Development utilities
size-compare: clean
	@echo "=== Size Comparison ==="
	@echo "Building with debug..."
	@make debug > /dev/null 2>&1
	@echo "Debug build size: $$(ls -la $(BUILD_DIR)/main_debug.ko | awk '{print $$5}') bytes"
	@echo "Building optimized..."
	@make all > /dev/null 2>&1
	@echo "Optimized build size: $$(ls -la $(BUILD_DIR)/main.ko | awk '{print $$5}') bytes"
	@echo "Building obfuscated..."
	@make obfuscate > /dev/null 2>&1
	@echo "Obfuscated build size: $$(ls -la $(BUILD_DIR)/main_obf.ko | awk '{print $$5}') bytes"

# Help target
help:
	@echo "Available targets:"
	@echo "  make          - Build optimized module (no debug)"
	@echo "  make debug    - Build module with debug information"
	@echo "  make test     - Build and test optimized module"
	@echo "  make debug-test - Build and test debug module"
	@echo "  make obfuscate - Build fully obfuscated module (no debug)"
	@echo "  make obfuscate-test - Build and test obfuscated module"
	@echo "  make clean    - Clean all build artifacts"
	@echo "  make size-compare - Compare sizes of different builds"
	@echo "  make help     - Show this help"
	@echo ""
	@echo "Project structure:"
	@echo "  $(SRC_DIR)/     - C source and header files"
	@echo "  $(SCRIPTS_DIR)/ - Python obfuscation scripts"  
	@echo "  $(BUILD_DIR)/   - Build outputs and temporary files"

.PHONY: all debug test debug-test obfuscate obfuscate-test clean install install-debug install-obf uninstall uninstall-debug _run_test_sequence _run_test_sequence_obf size-compare help
