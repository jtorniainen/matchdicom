#!/usr/bin/env python3

import dicom
import os
import sys
import tifffile
import blessings

# Maps DICOM files to RAW files using timestamps
# Usage: ./map-dicom DICOM RAW
#
# Script will print out files in the target directory that contain a matching timestamp.
#
# jtorniainen
# UEF 2017, MIT License

# TODO: Super slow right now because DICOM files are read completely just for meta information

term = blessings.Terminal()


def _get_raw_timestamp(raw_file):
    """ Returns the timestamp of the raw file """
    return raw_file.pages[0].tags['datetime'].value.decode('ascii')  # TODO: Add checks to see if this value exists


def _check_match(dicom_file, raw_file):
    timestamp_dicom = _get_dicom_timestamp(dicom_file)
    timestamp_raw = _get_raw_timestamp(raw_file)
    return timestamp_dicom == timestamp_raw


def _find_matching_files(dicom_file, raw_dir):
    raw_filenames = os.listdir(raw_dir)
    target_time = _get_dicom_timestamp(dicom_file)
    matches = []
    for raw_filename in raw_filenames:
            try:
                raw_file = tifffile.TiffFile(os.path.join(raw_dir, raw_filename))
                if target_time == _get_raw_timestamp(raw_file):
                    matches.append(raw_filename)
            except ValueError:
                print(term.red_bold('Warning: ') + '{} is not a TIFF file (skipped)'.format(raw_filename))
    return matches


def match_directories(dicom_dir, raw_dir):
    pass


def _get_dicom_comment(dicom_file):
    """ Returns the contents of the comment field of a dicom file """
    if hasattr(dicom_file, 'ImageComments'):
        return dicom_file.ImageComments
    else:
        return None


def _get_dicom_timestamp(dicom_file):
    if hasattr(dicom_file, 'AcquisitionDate'):
        datetime_str = '{}:{}:{} {}:{}:{}'.format(dicom_file.AcquisitionDate[0:4],
                                                  dicom_file.AcquisitionDate[4:6],
                                                  dicom_file.AcquisitionDate[6:8],
                                                  dicom_file.AcquisitionTime[0:2],
                                                  dicom_file.AcquisitionTime[2:4],
                                                  dicom_file.AcquisitionTime[4:6])

    else:
        datetime_str = None

    return datetime_str


def _print_dicom(filename, comment, timestamp):
    """ Pretty print the indentifiers of a DICOM file """

    if not comment:
        comment = '<None>'

    if not timestamp:
        timestamp = '<None>'

    dicom_str = (filename.ljust(20) +
                 term.magenta_bold(comment).ljust(60) +
                 term.yellow(timestamp))
    print(dicom_str)


def read_dicom_comments(path):
    """ Reads comments from all files found in path """

    if os.path.isdir(path):
        dicom_filenames = os.listdir(path)
        for dicom_filename in dicom_filenames:
            try:
                dicom_file = dicom.read_file(os.path.join(path, dicom_filename))
                dicom_comment = _get_dicom_comment(dicom_file)
                dicom_timestamp = _get_dicom_timestamp(dicom_file)
                _print_dicom(dicom_filename, dicom_comment, dicom_timestamp)

            except dicom.errors.InvalidDicomError:
                print(term.red_bold('WARNING:') + '{} not DICOM'.format(dicom_filename).rjust(20))
                continue

    else:
        try:
            dicom_file = dicom.read_file(path)
            dicom_comment = _get_dicom_comment(dicom_file)
            dicom_timestamp = _get_dicom_timestamp(dicom_file)
            _print_dicom(path, dicom_comment, dicom_timestamp)

        except dicom.errors.InvalidDicomError:
            print(term.red_bold('WARNING:').ljust(20) + '{} not DICOM'.format(path))


def run_from_cli():
    if len(sys.argv) == 2:  # Single file
        read_dicom_comments(sys.argv[1])

    elif len(sys.argv) == 3:  # Two files

        if os.path.isdir(sys.argv[1]) and os.path.isdir(sys.argv[2]):  # both dirs
            print('Not yet implemented')

        elif os.path.isdir(sys.argv[2]):  # dicom input is file -> raw input is dir
            dicom_file = dicom.read_file(sys.argv[1])
            matches = _find_matching_files(dicom_file, sys.argv[2])
            print(matches)

        else:  # both inputs are files
            dicom_file = dicom.read_file(sys.argv[1])
            raw_file = tifffile.TiffFile(sys.argv[2])
            check_result = _check_match(dicom_file, raw_file)

            if check_result:
                print(term.green_bold('**MATCH**'))
            else:
                print(term.yellow('NO-MATCH'))
    else:
        print('match-dicom takes exactly TWO input arguments! ')
