CC ?= gcc
CFLAGS ?= -Wall -Wextra -O2
LDLIBS ?= -lusb-1.0

all: relay_test

relay_test: relay_test.c
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)

clean:
	rm -f relay_test
