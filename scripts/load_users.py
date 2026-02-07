import re
import uuid
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ENV_FILE = Path(__file__).parent / ".." / ".env"
load_dotenv(ENV_FILE)

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
NON_PHONE_CHARS = re.compile(r"[^\d+]")


def clean_email(value: str | None) -> str | None:
    if value is None:
        return None

    value = str(value).strip()

    if value == "" or value.lower() == "<null>":
        return None

    if not EMAIL_REGEX.match(value):
        return None

    return value.lower()


def clean_phone(value: str | None, mobile_only: bool = True) -> str | None:
    import phonenumbers
    from phonenumbers.phonenumberutil import (
        NumberParseException,
        PhoneNumberType,
        number_type,
    )

    if value is None:
        return None

    value = str(value).strip()

    if value == "" or value.lower() == "<null>":
        return None

    # Remove everything except digits and +
    value = NON_PHONE_CHARS.sub("", value)

    # Normalize 00 → +
    if value.startswith("00"):
        value = "+" + value[2:]

    # If no + but all digits, try assuming international format
    if not value.startswith("+"):
        if not value.isdigit():
            return None
        value = "+" + value

    try:
        parsed = phonenumbers.parse(value, None)
    except NumberParseException:
        return None

    if not phonenumbers.is_valid_number(parsed):
        return None

    if mobile_only:
        n_type = number_type(parsed)
        if n_type not in (
            PhoneNumberType.MOBILE,
            PhoneNumberType.FIXED_LINE_OR_MOBILE,
        ):
            return None

    return phonenumbers.format_number(
        parsed,
        phonenumbers.PhoneNumberFormat.E164,
    )


def get_trimmed(row: pd.Series, key: str) -> str | None:
    value = row.get(key)

    if value is None:
        return None

    value = str(value).strip()

    if value == "" or value.lower() == "<null>":
        return None

    return value


def main() -> None:
    from echo.store.store import DuckDBStore

    excel_path = Path(__file__).parent / ".." / "user_data.xlsx"
    df = pd.read_excel(excel_path)

    store = DuckDBStore.with_postgres(do_setup=True)

    for _, row in df.iterrows():
        user_id = str(uuid.uuid4())

        store.users.upsert_user(
            user_id=user_id,
            contact_id=get_trimmed(row, "CONTACTID"),
            opportunity_id=get_trimmed(row, "OPPORTUNITYID"),
            name=get_trimmed(row, "FIRSTNAME"),
            last_name=get_trimmed(row, "LASTNAME"),
            phone_number=clean_phone(get_trimmed(row, "mobile")),
            mail=clean_email(get_trimmed(row, "EMAIL")),
            market=get_trimmed(row, "MERCADO"),
            faculty=get_trimmed(row, "FACULTAD"),
            plancode=get_trimmed(row, "PLANCODE"),
            track=get_trimmed(row, "track"),
        )


if __name__ == "__main__":
    main()
