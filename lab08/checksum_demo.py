from checksum_utils import compute_checksum, verify_checksum


def run_test(name: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"{name}: {status}")


def main():
    data = b"Hello, checksum!"
    checksum = compute_checksum(data)
    run_test("valid ascii payload", verify_checksum(data, checksum))

    binary_data = bytes([0, 1, 2, 3, 250, 251, 252, 253])
    binary_checksum = compute_checksum(binary_data)
    run_test("valid binary payload", verify_checksum(binary_data, binary_checksum))

    corrupted = bytearray(data)
    corrupted[0] ^= 0x01
    run_test("corrupted payload detection", not verify_checksum(bytes(corrupted), checksum))


if __name__ == "__main__":
    main()
