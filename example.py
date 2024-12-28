from license_checker import LicenseChecker
import time


def main():
    checker = LicenseChecker(
        license_key="07731a9746f446a783064668", api_url="http://localhost:8000"
    )

    def protected_code():
        print("This code only runs if the license is valid!")
        time.sleep(2)
        print("Application completed successfully!")

    try:
        checker.get_hardware_id = lambda: "test-hardware-id"
        checker.check_and_run(protected_code)
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
