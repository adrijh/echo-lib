import os
from textwrap import dedent

CREATE_POSTGRES_SECRET_SQL = dedent(f"""
    CREATE SECRET (
        TYPE postgres,
        HOST '{os.environ["POSTGRES_HOST"]}',
        PORT {os.environ["POSTGRES_PORT"]},
        DATABASE {os.environ["POSTGRES_DB"]},
        USER '{os.environ["POSTGRES_USER"]}',
        PASSWORD '{os.environ["POSTGRES_PASSWORD"]}'
    );
""")

ATTACH_POSTGRES_SQL = "ATTACH '' AS postgres (TYPE postgres);"
