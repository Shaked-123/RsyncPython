import argparse
from rsync.multiple_copies import rsync_parallel

DEFAULT_BANDWIDTH = 1  # KB per sec


def parse_pairs(sources_and_destinations_string):
    sources_and_destinations = []
    for pair in sources_and_destinations_string.split(','):
        if len(pair.split(':')) != 2:
            raise Exception("Incorrect format, use --help")
        sources_and_destinations.append(tuple(pair.split(':')))
    return sources_and_destinations


def run():
    parser = argparse.ArgumentParser(description='Pythonic rsync command with multiple transfers')
    parser.add_argument('--pairs', type=str, required=True,
                        help='Comma-separated list of source:destination pairs (for example src1:dst1,src2:dst2)')
    parser.add_argument('--bandwidth', type=int, default=None,
                        help='Optional bandwidth limit in KB')
    args = parser.parse_args()

    try:
        src_dst_pairs = parse_pairs(args.pairs)
        bandwidth = args.bandwidth if args.bandwidth else DEFAULT_BANDWIDTH
        rsync_parallel(src_dst_pairs, bandwidth)

    except Exception as e:
        print(e)


if __name__ == '__main__':
    run()