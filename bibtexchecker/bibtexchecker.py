#!/usr/bin/env python3
import argparse

from bibtexparser import bibdatabase, bparser
import bibtexparser

# Argument parser
parser = argparse.ArgumentParser(
    description="Checks the bibtex layout.", epilog="Use carefully!"
)

# Needed arguments.
parser.add_argument('file', type=str, help='The bibtex file')
parser.add_argument('-m', '--mute', action='store_true', help='Mutes output for correct entries')
parser.add_argument('-e', '--errors', action='store_true', help='Prints only errors')

parser.add_argument('-a', '--all', action='store_true', help='Checks for all possible errors')
parser.add_argument('-f', '--fields', action='store_true', help='Checks for missing fields')
parser.add_argument('-k', '--keys', action='store_true', help='Checks the key formatting')
parser.add_argument('-s', '--abbreviations', action='store_true', help='Checks for abbreviations')
parser.add_argument('-n', '--names', action='store_true',
                    help='Checks the names of the authors and editors to be unified')
parser.add_argument('-c', '--editors', action='store_true', help='Checks for correctly abbreviated editor names')

__all__ = ['BibtexChecker']

ARTICLE = "article"
INPROCEEDINGS = "inproceedings"
BOOK = "book"
PROCEEDINGS = "proceedings"
PHDTHESIS = "phdthesis"
TECHREPORT = "techreport"

# STANDARD_TYPE = ['article', 'book', 'booklet', 'conference', 'inbook', 'incollection', 'inproceedings', 'manual',
#                  'mastersthesis', 'misc', 'phdthesis', 'proceedings', 'techreport', 'unpublished']

FIELDS = dict()
FIELDS[ARTICLE] = [['title', 'author', 'journal', 'year', 'volume', 'pages'],
                   ['title', 'author', 'journal', 'year', 'volume', 'number', 'pages']]
FIELDS[INPROCEEDINGS] = [['title', 'author', 'editor', 'booktitle', 'publisher', 'address', 'pages', 'year'],
                         ['title', 'author', 'booktitle', 'publisher', 'pages', 'year'],
                         ['title', 'author', 'editor', 'booktitle', 'publisher', 'address', 'pages', 'year', 'series',
                          'volume'],
                         ['title', 'author', 'booktitle', 'publisher', 'pages', 'year', 'series', 'volume']]
FIELDS[BOOK] = [['title', 'author', 'publisher', 'address', 'year'],
                ['title', 'author', 'publisher', 'address', 'year', 'series', 'volume']]
FIELDS[PROCEEDINGS] = [['editor', 'title', 'publisher', 'address', 'year'],
                       ['editor', 'title', 'publisher', 'address', 'year', 'series', 'volume']]
FIELDS[PHDTHESIS] = [['author', 'title', 'school', 'year', 'type'],
                     ['author', 'title', 'school', 'year', 'month', 'type']]
FIELDS[TECHREPORT] = [['author', 'title', 'institution', 'year', 'month', 'type', 'number']]

ABBREVIATE = dict()
ABBREVIATE[ARTICLE] = ['journal']
ABBREVIATE[INPROCEEDINGS] = ['booktitle']
ABBREVIATE[BOOK] = list()
ABBREVIATE[PROCEEDINGS] = ['title']
ABBREVIATE[PHDTHESIS] = list()
ABBREVIATE[TECHREPORT] = list()

ABBREVIATIONS = [('Proceedings', 'Proc.'), ('Symposium', 'Symp.'), ('International', 'Int\'l'), ('Journal', 'J.'),
                 ('Distributed', 'Distr.')]
FUELLWOERTER = ['on', 'of', 'the']


def list_to_str(lst):
    string = ""
    i = 1
    for l in lst:
        string = string + str(l)
        if i < len(lst):
            string = string + ", "
        i = i + 1
    return string


class BibtexChecker(object):
    def __init__(self, mute=False, errors=False, check_all=True, check_fields=True, check_abbrs=True, check_keys=True,
                 check_names=True, check_editors=True):
        self.mute = mute
        self.errors = errors
        self.check_all = check_all
        if check_all:
            self.check_keys = True
            self.check_abbrs = True
            self.check_fields = True
            self.check_names = True
            self.check_editors = True
        else:
            self.check_keys = check_keys
            self.check_abbrs = check_abbrs
            self.check_fields = check_fields
            self.check_names = check_names
            self.check_editors = check_editors

        self.buffer = ""
        self.bib_parser = bparser.BibTexParser()
        self.bib_parser.ignore_nonstandard_types = False
        self.bib_parser.homogenise_fields = False

    def check(self, bibtex_str):
        bib_db = bibtexparser.loads(bibtex_str, self.bib_parser)
        if self.check_all or self.check_keys:
            self._check_duplicated_key(bib_db.entries)
            self._check_key_format(bib_db.entries)
        for record in bib_db.entries:
            correct = self._check_record(record)
            if self.errors and not correct or not self.errors:
                print(
                    "Checking entry for '" + record['ENTRYTYPE'] + "' with key '" + record['ID'] + "'\n" + self.buffer)
                self.buffer = ""
        # print(bib_db.entries)

    def check_file(self, file):
        self.check(file.read())

    def _check_record(self, record):
        correct = True
        if self.check_all or self.check_fields:
            correct = correct and self._check_missing_fields(record)
        if self.check_abbrs:
            correct = correct and self._check_possible_abbreviate(record)
        if correct:
            if not self.mute and not self.errors:
                self.buffer += "BibTex entry seems to be correct\n"
        return correct

    def _check_duplicated_key(self, records):
        keys = set()
        for record in records:
            if record['ID'] not in keys:
                keys.add(record['ID'])
            else:
                self.buffer += "Found duplicated key '" + record['ID'] + "'\n"

    def _check_key_format(self, records):
        for record in records:
            pass  # first letters of authors and year, inproc. 4 authors if > 4 than 4 with + and year

    def _check_missing_fields(self, record):
        fields = FIELDS[record['ENTRYTYPE']]
        missing_fields = list()
        for f in fields:
            absent = False
            variant_fields = list()
            for field in f:
                if field not in record:
                    absent = True
                    variant_fields.append(field)
            if absent:
                missing_fields.append(variant_fields)

        if len(fields) == len(missing_fields):
            self.buffer += "Missing fields for '" + record['ENTRYTYPE'] + "' with key '" + record[
                'ID'] + "' detected.\n"
            i = 1
            for variant_fields in missing_fields:
                self.buffer += "Missing fields are: " + list_to_str(variant_fields) + "\n"
                if i < len(missing_fields):
                    self.buffer += "OR\n"
                i = i + 1
            return False
        return True

    def _check_possible_abbreviate(self, record):
        correct = True
        for field in ABBREVIATE[record['ENTRYTYPE']]:
            field_value = record[field]
            abbreviate = list()  # "Possible abbreviation found: "
            for to_abr, abr in ABBREVIATIONS:
                if to_abr in field_value:
                    correct = False
                    abbreviate.append(to_abr + " can be abbreviated with " + abr)
            if len(abbreviate) > 0:
                self.buffer += "Possible abbreviation found for field '" + field + "': " + list_to_str(
                    abbreviate) + "\n"
        return correct


if __name__ == '__main__':
    args = parser.parse_args()

    bib_db_file = args.file
    mute_correct = args.mute
    only_errors = args.errors
    c_all = args.all
    c_abbrs = args.abbreviations
    c_keys = args.keys
    c_fields = args.fields
    c_names = args.names
    c_editors = args.editors

    bc = BibtexChecker(mute_correct, only_errors, check_all=c_all, check_abbrs=c_abbrs, check_keys=c_keys,
                       check_fields=c_fields, check_names=c_names, check_editors=c_editors)
    with open(bib_db_file) as bib_file:
        bc.check_file(bib_file)
