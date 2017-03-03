import sys
import os
import csv

import pyclan


region_keys = ('subregion', 'silence', 'skip')


def extract_region_comments(comments):
    results = [comment for comment in comments
               if any(x in comment.line
                      for x in region_keys)]
    return results

def group_comments(comments):

    silences = [(comment.time_onset, comment.time_offset)
                for comment in comments
                if "silence" in comment.line]

    subregions = [(comment.time_onset, comment.time_offset)
                  for comment in comments
                  if "subregion" in comment.line]

    skips = [(comment.time_onset, comment.time_offset)
             for comment in comments
             if "skip" in comment.line]

    if any(len(x) % 2 != 0 for x in [subregions, silences, skips]):
        raise Exception("had an uneven region group", comments)

    # skips_and_silences = list(set(skips + silences))
    # skips_and_silences.sort(key=lambda x: x[0])
    subregions.sort(key=lambda x: x[0])
    silences.sort(key=lambda x: x[0])
    skips.sort(key=lambda x: x[0])
    subregions = group_regions(subregions)
    silences = group_regions(silences)
    skips = group_regions(skips)

    return subregions, silences, skips


def group_regions(regions):
    results = []
    it = iter(regions)
    for x in it:
        results.append((x[1], next(it)[1]))
    return results

def walk_tree(dir):
    results = []
    fail_count = 0
    with open('errors.txt', 'wb') as err_out:
        for root, dirs, files in os.walk(dir):
            for file in files:
                if file.endswith(".cha"):
                    print "parsing file:  {}".format(file)
                    clan_file = pyclan.ClanFile(os.path.join(root, file))
                    comments = clan_file.get_user_comments()
                    regions = extract_region_comments(comments)
                    try:
                        subregions, silences, skips = group_comments(regions)
                        subrg_time = sum(x[1]-x[0] for x in subregions)
                        silen_time = sum(x[1] - x[0] for x in silences)
                        skips_time = sum(x[1] - x[0] for x in skips)
                        results.append([file, clan_file.total_time, subrg_time, silen_time, skips_time])
                    except Exception as e:
                        msg, regions = e.args
                        print msg
                        fail_count += 1
                        err_out.write("{}\n\n".format(file))
                        err_out.writelines([comment.line for comment in regions])
                        err_out.write("\n\n\n")

    print "\n\n\nfailed file count:  {}".format(fail_count)
    return results




if __name__ == "__main__":

    start_dir = sys.argv[1]
    output = sys.argv[2]

    results = walk_tree(start_dir)

    with open(output, "wb") as out:
        writer = csv.writer(out)
        writer.writerow(['file', 'total', 'subregion', 'silence', 'skip'])
        writer.writerows(results)


