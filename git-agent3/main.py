# main.py

import logging
from config import FLAG_PATH, POLL_INTERVAL, LOG_LEVEL


from file_flag import FileFlag, DefaultFlagHandler

def main():
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = DefaultFlagHandler()
    bridge  = FileFlag(
        flag_path=FLAG_PATH,
        interval=POLL_INTERVAL,
        handler=handler
    )
    bridge.start_polling()

if __name__ == "__main__":
    main()
