#include <libusb-1.0/libusb.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DCTTECH_VENDOR_ID 0x16c0
#define DCTTECH_PRODUCT_ID 0x05df
#define HID_SET_REPORT 0x09
#define HID_GET_REPORT 0x01
#define HID_REPORT_TYPE_FEATURE 0x03

typedef struct
{
    int index;
    uint8_t bus;
    uint8_t address;
    bool use_bus_address;
} DeviceSelector;

static void usage(const char *argv0)
{
    fprintf(stderr,
            "Usage:\n"
            "  %s list\n"
            "  %s [--index N] on <relay-index|all>\n"
            "  %s [--index N] off <relay-index|all>\n"
            "  %s [--index N] try <relay-index>\n"
            "  %s [--index N] status\n"
            "  %s [--bus B --addr A] on <relay-index|all>\n",
            argv0, argv0, argv0, argv0, argv0, argv0);
}

static void list_usb_devices(libusb_context *ctx)
{
    libusb_device **devices = NULL;
    ssize_t count = libusb_get_device_list(ctx, &devices);
    if (count < 0)
    {
        fprintf(stderr, "libusb_get_device_list failed: %s\n", libusb_error_name((int)count));
        return;
    }

    for (ssize_t i = 0; i < count; i++)
    {
        struct libusb_device_descriptor desc;
        if (libusb_get_device_descriptor(devices[i], &desc) != 0)
        {
            continue;
        }

        printf("%04x:%04x bus=%u addr=%u",
               desc.idVendor,
               desc.idProduct,
               libusb_get_bus_number(devices[i]),
               libusb_get_device_address(devices[i]));

        if (desc.idVendor == DCTTECH_VENDOR_ID && desc.idProduct == DCTTECH_PRODUCT_ID)
        {
            static int relay_index = 0;
            printf("  <-- USBRelay index=%d", relay_index);
            relay_index++;
        }
        printf("\n");
    }

    libusb_free_device_list(devices, 1);
}

static libusb_device_handle *open_relay(libusb_context *ctx, DeviceSelector selector)
{
    libusb_device **devices = NULL;
    ssize_t count = libusb_get_device_list(ctx, &devices);
    if (count < 0)
    {
        fprintf(stderr, "libusb_get_device_list failed: %s\n", libusb_error_name((int)count));
        return NULL;
    }

    libusb_device *selected = NULL;
    int relay_index = 0;

    for (ssize_t i = 0; i < count; i++)
    {
        struct libusb_device_descriptor desc;
        if (libusb_get_device_descriptor(devices[i], &desc) != 0)
        {
            continue;
        }

        if (desc.idVendor != DCTTECH_VENDOR_ID || desc.idProduct != DCTTECH_PRODUCT_ID)
        {
            continue;
        }

        const uint8_t bus = libusb_get_bus_number(devices[i]);
        const uint8_t address = libusb_get_device_address(devices[i]);

        if (selector.use_bus_address)
        {
            if (bus == selector.bus && address == selector.address)
            {
                selected = devices[i];
                break;
            }
        }
        else if (relay_index == selector.index)
        {
            selected = devices[i];
            break;
        }

        relay_index++;
    }

    libusb_device_handle *handle = NULL;
    if (selected)
    {
        int ret = libusb_open(selected, &handle);
        if (ret != 0)
        {
            fprintf(stderr, "open relay failed: %s\n", libusb_error_name(ret));
            handle = NULL;
        }
    }

    libusb_free_device_list(devices, 1);

    if (!handle)
    {
        if (selector.use_bus_address)
        {
            fprintf(stderr, "Relay not found: expected VID:PID %04x:%04x bus=%u addr=%u\n",
                    DCTTECH_VENDOR_ID, DCTTECH_PRODUCT_ID, selector.bus, selector.address);
        }
        else
        {
            fprintf(stderr, "Relay not found: expected VID:PID %04x:%04x index=%d\n",
                    DCTTECH_VENDOR_ID, DCTTECH_PRODUCT_ID, selector.index);
        }
        return NULL;
    }

    if (libusb_kernel_driver_active(handle, 0) == 1)
    {
        libusb_detach_kernel_driver(handle, 0);
    }

    return handle;
}

static int send_feature(libusb_device_handle *handle, unsigned char command, unsigned char relay)
{
    unsigned char report[8] = {0};
    report[0] = command;
    report[1] = relay;

    int ret = libusb_control_transfer(
        handle,
        LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_CLASS | LIBUSB_RECIPIENT_INTERFACE,
        HID_SET_REPORT,
        HID_REPORT_TYPE_FEATURE << 8,
        0,
        report,
        sizeof(report),
        1000);

    if (ret < 0)
    {
        fprintf(stderr, "set feature failed: %s\n", libusb_error_name(ret));
        return 1;
    }

    return 0;
}

static int send_feature_variant(libusb_device_handle *handle, const unsigned char *report, int report_len, int report_id)
{
    int ret = libusb_control_transfer(
        handle,
        LIBUSB_ENDPOINT_OUT | LIBUSB_REQUEST_TYPE_CLASS | LIBUSB_RECIPIENT_INTERFACE,
        HID_SET_REPORT,
        (HID_REPORT_TYPE_FEATURE << 8) | report_id,
        0,
        (unsigned char *)report,
        (uint16_t)report_len,
        1000);

    if (ret < 0)
    {
        fprintf(stderr, "variant failed: %s\n", libusb_error_name(ret));
        return 1;
    }

    return 0;
}

static void print_report(const char *label, const unsigned char *report, int len)
{
    printf("%s:", label);
    for (int i = 0; i < len; i++)
    {
        printf(" %02x", report[i]);
    }
    printf("\n");
}

static int try_variants(libusb_device_handle *handle, unsigned char relay)
{
    unsigned char variants[][9] = {
        {0x00, 0xff, relay, 0, 0, 0, 0, 0, 0},
        {0xff, relay, 0, 0, 0, 0, 0, 0, 0},
        {0x00, relay, 0xff, 0, 0, 0, 0, 0, 0},
        {0xff, 0x00, relay, 0, 0, 0, 0, 0, 0},
    };
    const int lengths[] = {9, 8};
    const int report_ids[] = {0, 1};

    for (size_t v = 0; v < sizeof(variants) / sizeof(variants[0]); v++)
    {
        for (size_t l = 0; l < sizeof(lengths) / sizeof(lengths[0]); l++)
        {
            for (size_t r = 0; r < sizeof(report_ids) / sizeof(report_ids[0]); r++)
            {
                print_report("sending", variants[v], lengths[l]);
                printf("report_id=%d len=%d\n", report_ids[r], lengths[l]);
                if (send_feature_variant(handle, variants[v], lengths[l], report_ids[r]) == 0)
                {
                    printf("sent ok; check relay click/LED now\n");
                }
            }
        }
    }

    return 0;
}

static int get_status(libusb_device_handle *handle)
{
    unsigned char report[9] = {0};

    int ret = libusb_control_transfer(
        handle,
        LIBUSB_ENDPOINT_IN | LIBUSB_REQUEST_TYPE_CLASS | LIBUSB_RECIPIENT_INTERFACE,
        HID_GET_REPORT,
        (HID_REPORT_TYPE_FEATURE << 8) | report[0],
        0,
        report,
        sizeof(report),
        1000);

    if (ret < 0)
    {
        fprintf(stderr, "get feature failed: %s\n", libusb_error_name(ret));
        return 1;
    }

    printf("raw status report:");
    for (int i = 0; i < ret; i++)
    {
        printf(" %02x", report[i]);
    }
    printf("\n");
    return 0;
}

static int parse_relay_index(const char *arg)
{
    if (strcmp(arg, "all") == 0)
    {
        return 255;
    }

    char *end = NULL;
    long value = strtol(arg, &end, 10);
    if (*arg == '\0' || *end != '\0' || value < 1 || value > 8)
    {
        return -1;
    }

    return (int)value;
}

int main(int argc, char **argv)
{
    libusb_context *ctx = NULL;
    int ret = libusb_init(&ctx);
    if (ret != 0)
    {
        fprintf(stderr, "libusb_init failed: %s\n", libusb_error_name(ret));
        return 1;
    }

    if (argc == 2 && strcmp(argv[1], "list") == 0)
    {
        list_usb_devices(ctx);
        libusb_exit(ctx);
        return 0;
    }

    DeviceSelector selector = {0};
    int argi = 1;

    while (argi < argc)
    {
        if (strcmp(argv[argi], "--index") == 0 && argi + 1 < argc)
        {
            selector.index = atoi(argv[argi + 1]);
            argi += 2;
            continue;
        }

        if (strcmp(argv[argi], "--bus") == 0 && argi + 1 < argc)
        {
            selector.bus = (uint8_t)atoi(argv[argi + 1]);
            selector.use_bus_address = true;
            argi += 2;
            continue;
        }

        if (strcmp(argv[argi], "--addr") == 0 && argi + 1 < argc)
        {
            selector.address = (uint8_t)atoi(argv[argi + 1]);
            selector.use_bus_address = true;
            argi += 2;
            continue;
        }

        break;
    }

    if (argi >= argc)
    {
        usage(argv[0]);
        libusb_exit(ctx);
        return 1;
    }

    libusb_device_handle *handle = open_relay(ctx, selector);
    if (!handle)
    {
        libusb_exit(ctx);
        return 1;
    }

    int exit_code = 0;

    const char *command = argv[argi];
    const int remaining = argc - argi;

    if (remaining == 1 && strcmp(command, "status") == 0)
    {
        exit_code = get_status(handle);
    }
    else if (remaining == 2 && strcmp(command, "try") == 0)
    {
        int relay = parse_relay_index(argv[argi + 1]);
        if (relay < 1 || relay > 8)
        {
            usage(argv[0]);
            exit_code = 1;
        }
        else
        {
            exit_code = try_variants(handle, (unsigned char)relay);
        }
    }
    else if (remaining == 2 && (strcmp(command, "on") == 0 || strcmp(command, "off") == 0))
    {
        int relay = parse_relay_index(argv[argi + 1]);
        if (relay < 0)
        {
            usage(argv[0]);
            exit_code = 1;
        }
        else if (strcmp(command, "on") == 0)
        {
            exit_code = send_feature(handle, relay == 255 ? 0xfe : 0xff, relay == 255 ? 0 : (unsigned char)relay);
        }
        else
        {
            exit_code = send_feature(handle, relay == 255 ? 0xfc : 0xfd, relay == 255 ? 0 : (unsigned char)relay);
        }
    }
    else
    {
        usage(argv[0]);
        exit_code = 1;
    }

    libusb_close(handle);
    libusb_exit(ctx);
    return exit_code;
}
