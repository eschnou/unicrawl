from pathlib import Path

import pandas as pd

from unicrawl.spiders.config.settings import YEAR


def merge_programs(school: str):
    """
    # TODO: complete desc
    Merge UCL and others? programs

    Note:
    After running unicrawl/spiders/{school}_programs.py, programs can be split over several lines
     (due to the way the website is organised. The goal of this function is to merge those lines
     to have one line per program
    """

    # Read the programs file
    programs_fn = \
        Path(__file__).parent.absolute().joinpath(f"../../data/crawling-output/{school}_programs_{YEAR}_pre.json")
    programs_df = pd.read_json(programs_fn).set_index("id")

    # TODO: there is probably a better way to do that
    # Group different keys
    programs_df_grouped = programs_df.groupby("id")
    programs_merged_df = programs_df_grouped["name"].unique().apply(lambda x: x[0]).to_frame()
    for key in ["campus", 'cycle', "faculty", "url"]:
        programs_merged_df[key] = programs_df_grouped[key].unique().apply(lambda x: x[0])
    programs_merged_df['courses'] = programs_df_grouped["courses"].sum()
    programs_merged_df['ects'] = programs_df_grouped["ects"].sum()

    # Remove redundant courses-ects couple
    def remove_doubles(x):
        courses, ects = zip(*list(set(zip(x.courses, x.ects))))
        x.courses = courses
        x.ects = ects
        return x
    programs_merged_df[["courses", "ects"]].apply(lambda x: remove_doubles(x), axis=1)

    programs_merged_fn = \
        Path(__file__).parent.absolute().joinpath(f"../../data/crawling-output/{school}_programs_{YEAR}.json")
    programs_merged_df.reset_index().to_json(programs_merged_fn, orient='records', indent=1)


def merge_courses(school: str):
    """
    # TODO: complete desc
    Merge Uantwerp and others? courses

    Note:
    After running unicrawl/spiders/{school}_coursess.py, courses can be split over several lines
     (due to the way the website is organised). The goal of this function is to merge those lines
     to have one line per course
    """

    # Read the programs file
    courses_fn = \
        Path(__file__).parent.absolute().joinpath(f"../../data/crawling-output/{school}_courses_{YEAR}_pre.json")
    courses_df = pd.read_json(courses_fn).set_index("id")

    # TODO: there is probably a better way to do that
    # Group different keys
    courses_df_grouped = courses_df.groupby("id")
    courses_merged_df = courses_df_grouped["name"].unique().apply(lambda x: x[0]).to_frame()
    for key in ["year", "url", "content"]:
        courses_merged_df[key] = courses_df_grouped[key].apply(lambda x: x[0])
    courses_merged_df['languages'] = courses_df_grouped["languages"].sum().apply(lambda x: list(set(x)))
    courses_merged_df['teachers'] = courses_df_grouped["teachers"].sum().apply(lambda x: list(set(x)))

    courses_merged_fn = \
        Path(__file__).parent.absolute().joinpath(f"../../data/crawling-output/{school}_courses_{YEAR}.json")
    courses_merged_df.reset_index().to_json(courses_merged_fn, orient='records', indent=1)


if __name__ == '__main__':
    # TODO: edit
    school = 'uantwerp'
    merge_courses(school)