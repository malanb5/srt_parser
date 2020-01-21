#!/usr/bin/python
"""
quick parsing script for parsing srt subtitle
files to a full transcript

Author: Matthew Bladek
"""

import pysrt, argparse, sys, logging, subprocess, os, yaml
import Utils.Quiet_Run

# init logger
logging.basicConfig()
logger = logging.getLogger('logger')

def is_language_file(file, language):
    """
    selects file based upon a language parameter
    :param file: the subtitle file
    :param language: the language as abbreviated in the subtitle file
    :return: boolean as to whether the file is in the right language or not
    """
    logger.info("File: %s, Langugage: %s" %(file, language))

    # parse the file name to check to see if english is in the header
    file_name_list = file.split('-')
    logger.info("File Language Piece: %s" %(file_name_list[1]))

    return file_name_list[1].find(language) != -1

def key_extract(tup, delim, first_index, second_index):
    """
    key extractor function to sort based upon the second element,
    select the first element split on "-"
    :param tup: the tuple to extract the key from
    :param delim: the delimiter to split the word up on
    :param first_index: the index of the tuple
    :param second_index: the index of the substring
    :return: the number extracted as the key
    """
    try:
        return int(tup[first_index].split(delim)[second_index])
    except:
        return 9999

def get_full_paths(root_dir, fn_l):
    """
    returns the full path of a file for a root directory and a list of files
    :param root_dir the root directory where the files are located
    :param fn_l the list of file names
    :return: a list of the full path file list
    """
    if(type(fn_l) is not list):
        raise Exception("the file name's list must be a list")

    fp_fn_l = list()
    for each_fn in fn_l:
        fp_fn_l.append("/".join([root_dir, each_fn]))
    return fp_fn_l

def extractor(word, index, delim):
    """
    splits a word based on a delimiter and then selects the substring based upon an index
    if the index is outside of the word list, then the index will be the last substring in the
    broken up word
    :param word: the word to be split up and a substring extracted from
    :param index: the index of the substring to be extracted from the word
    :param delim: the delimiter on which to split the word into pieces
    :return: the substring of word, given by the split on delim and the index
    """
    word_list = word.split(delim)

    if(len(word_list)<= index):
        index = len(word_list) - 1

    return word_list[index]

def is_correct_language(file_name, args):
    """
    selector function which determines if the file name is in the correct language
    :param file_name: the file name to determine if the correct language is selected
    :param args: a list of arguments
        [0]: the function to extract just the word to see if the language is in
        [1]: the language abbreviation to select
    :return: whether the file_name has selected the correct language
    """
    extract_fxn = globals()[args[0]]
    lang_abbr = args[1]
    index = args[2]
    delim = args[3]

    extracted_fn = extract_fxn(file_name, index, delim)

    return extracted_fn.find(lang_abbr) is not -1

def select_file(file_name, criteria_fns, critera_fns_args):
    """
    selects a file based upon a set of criteria
    :param file_name: the file name to be selected or not
    :param criteria_fn: a list of boolean functions that takes the file name as an argument and determines whether or not the
        criteria has been meet for each function
    :param critera_fns_args: the list of args that will be feed into each criteria function
    :return: whether the file is to be selected or not
    """
    for i in range(0, len(criteria_fns)):
        if not criteria_fns[i](file_name, critera_fns_args[i]):
            return False
    return True

def select_append(selector_fxn, dir, fn, criteria_fxns, criteria_args, build_list):
    """
    if the given function is true then append the selection to the list
    :param selector_fxn: the selector function
    :param dir: the directory where the file resides
    :param fn: the name of the file
    :param criteria_fxns: the criteria functions are a set of functions which will determine
    if the fn is to be selected or not
    :param criteria_args: the criteria args are additional arguments to each criteria function
    :param build_list: the list to append the
    """

    if (selector_fxn(fn, criteria_fxns, criteria_args)):
        build_list.append((dir, fn))

def get_files_recursive(root_dir, dir_list, critiera_fxns, criteria_args, root_fn_l):
    """
    recursively gets all of the files from the directories and appends it to a list of files
    is called recursively until all files have been obtained from all all levels of nested directories

    select files based upon a certain criteria function and args
    :param root_dir the root directory of where the directories are located
    :param dir_list a list of directories to get files from
    :param criteria_fxns: the criteria functions are a set of functions which will determine
    if the fn is to be selected or not
    :param criteria_args: the criteria args are additional arguments to each criteria function
    :param root_fn_l a list of path and file names
    :return: a list of all of the files in a list of directories
    """
    for each_dir in dir_list:
        fp_fn_l = get_full_paths(root_dir, [each_dir])

        for root, dirs, files in os.walk(fp_fn_l[0], topdown=True):
            if(len(dirs) != 0):
                get_files_recursive(dirs, root_fn_l)

            for each_file in files:
                select_append(select_file, root, each_file, critiera_fxns, criteria_args, root_fn_l)

def get_fxns_from_symbol_table(fxns_names):
    """
    gets the requested functions from the symbol table
    :param fxns_names: strings of the function names
    :return: a list of the functions
    """
    fxn_list = list()

    for each_fxn in fxns_names:
        fxn_list.append(globals()[each_fxn])
    return fxn_list

def get_sub_files(config_yaml):
    """
    :param config_yaml: the configuration dictionary
    :param config_yaml: temp_dir: the root directory where the file to parse are located
    :param delim (optional): splits the file based upon a delimiter, the default is '-'
    """
    root_dir = config_yaml["temp_dir"]
    root_fn_l = list() # a list of file names of the files to be parsed

    critiera_fxns = get_fxns_from_symbol_table(config_yaml["criteria_fxns"])
    criteria_args = config_yaml["criteria_args"]

    for root, dirs, files in os.walk(root_dir, topdown=True):
        get_files_recursive(root, dirs, critiera_fxns, criteria_args, root_fn_l)

        for each_file in files:
            select_append(select_file, root, each_file, critiera_fxns, criteria_args, root_fn_l)

    print_root_fn_l(root_fn_l)

    return root_fn_l


def get_args_in_sub():
    """
    subroutine to get the command line args
    :return: the command line args object
    """
    parser = init_parse_cl_args()
    args_in = parser.parse_args()
    return args_in

def merge_settings(args_in, config_yaml):
    """
    merge the command line arguments and yaml file configurations
    if a command line argument is present it will take precedence over the
    same yaml config setting.  a single yaml dictionary will be returned with
    the merged settings.
    :param config_yaml: a dictionary of the configuration from the yaml file
    :param args_in: a Namespace object containing the CL args
    :return: a dictionary of the merged settings from the CL and the yaml file
    """

    if (args_in.file_in != None):
        config_yaml["file_in"] = args_in.file_in
        logger.info("CL FOUND: UPDATING IN THE CONFIG DICTIONARY: %s", config_yaml["file_in"])

    if (args_in.file_to_write_to != None):
        config_yaml["file_to_write_to"] = args_in.file_to_write_to
        logger.info("CL FOUND: UPDATING IN THE CONFIG DICTIONARY: %s", config_yaml["file_to_write_to"])

    if (args_in.lang != None):
        config_yaml["lang_abbr"] = args_in.lang
        logger.info("CL FOUND: UPDATING IN THE CONFIG DICTIONARY: %s", config_yaml["lang_abbr"])

def print_root_fn_l(root_fn_l):
    """
    prints out the list of tuples of the root and file name
    :param root_fn_l: list of tuples of the root and file name
    """
    for each_r, each_f in root_fn_l:
        logger.info("Root: %s, File: %s", each_r, each_f)

def write_subheader(root, file_to_write, fn, folder_format):
    """
    writes subheaders to the output file, each file name is the subheading
    a folder that contains the files will be the major heading
    there are two modes:
              subfolder: indicate that the zip has subfolders where the subtitles are broken down by module
              regular:   indicates that the zip has no subfolders, the subtitles are directly in the folder
    :param root: the location of the files
    :param file_to_write: the output file to write to
    :param fn: the file name
    :param folder_format: subfolder - if the directory structure is broken down by subfolders, regular - if the directory
        contains regular subtitle files
    """

    seen_dirs = []

    if(folder_format == "subfolder"):
        if root not in seen_dirs:
            sub_root = root[(root.rfind('/')) + 1:] + " : " + fn[:-4]
            file_to_write.write("\n\n" + sub_root + "\n\n")
            file_lines = get_text_from_subs(root + "/" + fn)
        else:
            seen_dirs.append(root)

    elif (folder_format == "regular"):
        logger.debug("regular file formatting")
        file_list = fn.split("-")
        counter = 1

        # always add the first part of the header
        header = "\n\n"
        header += file_list[0]

        while(counter < len(file_list)):

            if(file_list[counter].find("lang") != -1):
                break
            else:
                header += " - "
                header += file_list[counter]
                counter += 1

        header += "\n\n"
        file_to_write.write(header)
    else:
        raise Exception("Invalid option must be subfolder or regular.")


def get_text_from_subs(file_path):
    """
    opens a subtitle srt file, returns a string of all of the text in the subtitle file
    :param file_path: the path to the file
    :return: a string of the subtitles
    """""
    subs = pysrt.open(file_path)

    text = str()

    for line in subs:
        curr_line = line.text
        curr_line_len = len(curr_line)
        if curr_line_len == 0:
            continue
        else:
            text += curr_line
            text+= " "

    return text

def write_transcript(root_fn_l, config_yaml):
    """
    writes out the transcript from the list of files
    :param root_fn_l the sorted list of tuples of the file path and the file name
    """

    with open(config_yaml["file_to_write_to"], "w+") as file_to_write:
        for each in root_fn_l:
            root = each[0]
            file = each[1]

            write_subheader(root, file_to_write, file, "regular")

            file_lines = get_text_from_subs(root + "/" + file)
            file_to_write.writelines(file_lines)

def parse_srt(config_yaml):
    """
    parses the zipped srt archive into a single transcript file
    :param config_yaml: a dictionary of settings to parse the srt archive
    :return: a string of the srt contents concatenated together, selected by the language,
     and ordered in ascending numerical order
    """

    # the temp dir is where the subtitle files will be unzipped to
    temp_dir = config_yaml["temp_dir"]

    # unzips the files to the temporary directory
    subprocess.call(["unzip", config_yaml["zipped_sub_file"], "-d", temp_dir])

    root_fn_l = get_sub_files(config_yaml)
    return root_fn_l


def main(config_yaml):
    args_in = get_args_in_sub()

    logger.setLevel(logging.DEBUG)
    logger.info('Starting the Subtitle Parser Script')

    merge_settings(args_in, config_yaml)

    root_fn_l = parse_srt(config_yaml)

    root_fn_l.sort(key=lambda key: key_extract(key, "-", 1, 0))

    write_transcript(root_fn_l, config_yaml)

    # delete the temporary files
    subprocess.call(["rm", "-rf", config_yaml["temp_dir"]])

    logger.info('success: output written to: %s' %(config_yaml["file_to_write_to"]))

if __name__ == '__main__':
    with open("config.yaml") as config_file:
        config_yaml = yaml.safe_load(config_file)

    logger.setLevel(logging.DEBUG)
    logger.info(config_yaml)
    prereqs = config_yaml["preqs"]


    # set the encoding and python version
    Python3 = sys.version_info[0] == config_yaml["python_version"]
    Encoding= config_yaml["Encoding"]

    Utils.Quiet_Run.check_prereqs(prereqs)
    main(config_yaml)


def init_parse_cl_args():
    """
    creates an object parser to process the command line args
    :return: an object to parse the command line args
    """
    parser = argparse.ArgumentParser(description="Subtitle to Transcript Parser")

    parser.add_argument('--fileout', '-fo',
                        dest="file_to_write_to",
                        type=str,
                        help="the file to write the subtitles to.")

    parser.add_argument('--filein', '-fin',
                        dest="file_in",
                        type=str,
                        required=True,
                        help="the zipped subtitle archive containing the subtitles.")

    parser.add_argument('--language', '-l',
                        dest="lang",
                        type=str,
                        help="the language to parse, abbreviated (eg. English would be en), \n"
                             "if the subtitles do not specify a language then do not include \n"
                             "this argument.  Language cannot be ^&null, which is the default\n"
                             "language to indicate that no language has been selected")
    return parser