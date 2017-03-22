#!/usr/bin/env python3

import dicom
import os
import tifffile
import blessings
import datetime
import argparse

# Maps DICOM files to RAW files using timestamps
# Usage: ./map-dicom DICOM RAW
#
# Script will print out files in the target directory that contain a matching timestamp.
#
# jtorniainen
# UEF 2017, MIT License


term = blessings.Terminal()


def _check_match(dicom_file, raw_file):
    """ Check if the timestamp of a DICOM file matches the timestamp of a RAW file """
    timestamp_dicom = _get_dicom_timestamp(dicom_file)
    timestamp_raw = _get_raw_timestamp(raw_file)
    return timestamp_dicom == timestamp_raw


def _find_matching_files(dicom_file, raw_dir, verbose=False):
    """ Searches a directory for matching RAW files """
    raw_filenames = os.listdir(raw_dir)
    target_time = _get_dicom_timestamp(dicom_file)
    matches = []
    for raw_filename in raw_filenames:
            try:
                raw_file = tifffile.TiffFile(os.path.join(raw_dir, raw_filename))
                raw_timestamp = _get_raw_timestamp(raw_file)

                if verbose:
                    print(term.yellow_bold('Checking: ') + '{} vs. {} ({})'.format(target_time,
                                                                                   raw_timestamp,
                                                                                   raw_filename))

                if target_time == raw_timestamp:
                    print(term.green_bold('Found: ') + '{} is a match'.format(raw_filename))
                    matches.append(raw_filename)

            except ValueError:
                print(term.red_bold('Warning: ') + '{} is not a TIFF file (skipped)'.format(raw_filename))
    return matches


def match_directories(dicom_dir, raw_dir):
    """ Finds matching files in two directories (one DICOM and one RAW) """
    matches = {}
    dicom_filenames = os.listdir(dicom_dir)
    for dicom_filename in dicom_filenames:
        try:
            dicom_file = dicom.read_file(os.path.join(dicom_dir, dicom_filename), stop_before_pixels=True)
            matches[dicom_filename] = _find_matching_files(dicom_file, raw_dir)
        except dicom.errors.InvalidDicomError:
            print(term.red_bold('WARNING: ') + '{} is not a DICOM-file!'.format(dicom_filename).rjust(20))
            continue
    return matches


def _get_dicom_comment(dicom_file):
    """ Returns the contents of the comment field of a dicom file """
    if hasattr(dicom_file, 'ImageComments'):
        return dicom_file.ImageComments
    else:
        return None


# -------------------- FILE HANDLERS --------------------

def open_dicom(path):
    return dicom.read_file(path, stop_before_pixels=True)


def open_raw(path):
    return tifffile.TiffFile(path)

# TIMESTAMPS


def _get_raw_timestamp(raw_file):
    """ Returns the timestamp of the raw file """
    timestamp_str = raw_file.pages[0].tags['datetime'].value.decode('ascii')
    return datetime.datetime.strptime(timestamp_str, '%Y:%m:%d %H:%M:%S')


def _get_dicom_timestamp(dicom_file):
    """ Gets the timestamp from a DICOM file """
    if hasattr(dicom_file, 'AcquisitionDate'):
        timestamp_str = '{}:{}:{} {}:{}:{}'.format(dicom_file.AcquisitionDate[0:4],
                                                   dicom_file.AcquisitionDate[4:6],
                                                   dicom_file.AcquisitionDate[6:8],
                                                   dicom_file.AcquisitionTime[0:2],
                                                   dicom_file.AcquisitionTime[2:4],
                                                   dicom_file.AcquisitionTime[4:6])

        return datetime.datetime.strptime(timestamp_str, '%Y:%m:%d %H:%M:%S')

    else:
        return None


# PRINTING FUNCTIONS

def _print_metadata(filename, comment, timestamp):
    """ Pretty print the metadata of a DICOM/RAW file """

    if not comment:
        comment = '<None>'

    if not timestamp:
        timestamp = '<None>'
    else:
        timestamp = str(timestamp)

    print(filename.ljust(60) + term.magenta_bold(comment).ljust(60) + term.yellow(timestamp))


def print_dicom_metadata(path):
    """ Reads comments and timestamps from all DICOM files found in path """

    if os.path.isdir(path):
        for dicom_filename in os.listdir(path):
            try:
                dicom_file = open_dicom(os.path.join(path, dicom_filename))
                dicom_comment = _get_dicom_comment(dicom_file)
                dicom_timestamp = _get_dicom_timestamp(dicom_file)
                _print_metadata(dicom_filename, dicom_comment, dicom_timestamp)

            except dicom.errors.InvalidDicomError:
                print(term.red_bold('WARNING: ') + '{} not DICOM'.format(dicom_filename))
                continue

            except IsADirectoryError:
                print(term.red_bold('WARNING: ') + '{} is a directory'.format(dicom_filename))
                continue
    else:
        try:
            dicom_file = open_dicom(path)
            dicom_comment = _get_dicom_comment(dicom_file)
            dicom_timestamp = _get_dicom_timestamp(dicom_file)
            _print_metadata(path, dicom_comment, dicom_timestamp)

        except dicom.errors.InvalidDicomError:
            print(term.red_bold('WARNING: ') + '{} not DICOM'.format(path))


def print_raw_metadata(path):
    """ Reads comments and timestamps from all RAW files found in path """

    if os.path.isdir(path):
        for raw_filename in os.listdir(path):
            try:
                raw_file = open_raw(os.path.join(path, raw_filename))
                raw_comment = ''
                raw_timestamp = _get_raw_timestamp(raw_file)
                _print_metadata(raw_filename, raw_comment, raw_timestamp)

            except ValueError:
                print(term.red_bold('WARNING: ') + '{} not RAW'.format(raw_filename))
                continue

            except IsADirectoryError:
                print(term.red_bold('WARNING: ') + '{} is a directory'.format(raw_filename))
                continue
    else:
        try:
            raw_file = open_raw(path)
            raw_comment = ''
            raw_timestamp = _get_raw_timestamp(raw_file)
            _print_metadata(path, raw_comment, raw_timestamp)

        except ValueError:
            print(term.red_bold('WARNING: ').ljust(20) + '{} not RAW'.format(path))


def print_matching_files(matches):
    """ Pretty print matches-dict """
    for key, value in matches.items():
        print(term.bold_yellow(key).ljust(40) + ' -> ' + term.green(str(value)))


def print_comparison(dicom_filename, raw_filename):
    """ Print the comparison of meta data from a DICOM-RAW pair """
    try:
        dicom_data = open_dicom(dicom_filename)
    except dicom.errors.InvalidDicomError:
        print(term.red_bold('WARNING: ') + '{} not DICOM'.format(dicom_filename))
        return

    try:
        raw_data = open_raw(raw_filename)
    except ValueError:
        print(term.red_bold('WARNING: ').ljust(20) + '{} not RAW'.format(raw_filename))
        return

    dicom_time = _get_dicom_timestamp(dicom_data)
    dicom_comment = _get_dicom_comment(dicom_data)

    raw_time = _get_raw_timestamp(raw_data)

    time_diff = max([dicom_time, raw_time]) - min([dicom_time, raw_time])
    dicom_filename = os.path.basename(dicom_filename)
    raw_filename = os.path.basename(raw_filename)

    name_dicom = dicom_filename.ljust(30)
    name_raw = raw_filename.ljust(30)
    time_raw = term.yellow(str(raw_time))
    time_dicom = term.yellow(str(dicom_time))
    if time_diff.total_seconds() > 2:
        time_diff = ' (Δ=' + term.red(str(time_diff)) + ') '
    else:
        time_diff = ' (Δ=' + term.green(str(time_diff)) + ') '
    comment_dicom = term.magenta(dicom_comment).ljust(60)
    print(name_dicom + comment_dicom + time_dicom + time_diff + time_raw, name_raw)


# MAIN--------------------------------------------------

def run_from_cli():

    parser = argparse.ArgumentParser()
    parser.add_argument('targets', nargs='*')
    parser.add_argument('-r', help='Access meta-data of RAW files', action='store_true')
    args = parser.parse_args()

    if len(args.targets) == 1:  # Single file or directory
        if args.r:
            print_raw_metadata(args.targets[0])
        else:
            print_dicom_metadata(args.targets[0])

    elif len(args.targets) == 2:  # Two files (this branch is probably now broken)

        if os.path.isdir(args.targets[0]) and os.path.isdir(args.targets[1]):  # both dirs
            pass
            # matches = match_directories(sys.argv[1], sys.argv[2])
            # print_matching_files(matches)

        elif os.path.isdir(args.targets[1]):
            for raw_file in os.listdir(args.targets[1]):
                print_comparison(args.targets[0], os.path.join(args.targets[1], raw_file))

        else:  # both inputs are files
            print_comparison(args.targets[0], args.targets[1])
