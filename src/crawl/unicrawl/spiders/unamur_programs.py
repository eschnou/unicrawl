# -*- coding: utf-8 -*-

import os
import sys

import scrapy
from scrapy.crawler import CrawlerProcess

import config.utils as u
from config.settings import YEAR

sys.path.append(os.getcwd())

BASE_URL = "https://directory.unamur.be/teaching/programmes"


class UNamurProgramSpider(scrapy.Spider):
    name = "unamur-programs"
    custom_settings = {
        'FEED_URI': f'../../data/crawling-output/unamur_programs_{YEAR}.json',
    }

    def start_requests(self):
        yield scrapy.Request(BASE_URL, self.parse)

    def parse(self, response):
        # Get list of faculties
        faculties = response.xpath(f"//div[@id='tab-{YEAR}']//h3/a/text()").getall()
        for faculty in faculties:
            # For each faculty get its programs
            programs_links = response.xpath(
                f"//div[@id='tab-{YEAR}']//h3[a[contains(text(), \"{faculty}\")]]"
                f"//following::div[1]/div/a/@href").getall()
            programs_names = response.xpath(
                f"//div[@id='tab-{YEAR}']//h3[a[contains(text(), \"{faculty}\")]]"
                f"//following::div[1]/div/a/text()").getall()
            for program_name, programs_link in zip(programs_names, programs_links):
                # Scrap only bachelor and master programs
                # TODO: devrait-on rajouter les certificats?
                if program_name.startswith("Bachelier") or program_name.startswith("Master"):
                    cycle = 'bachelor' if program_name.startswith("Bachelier") else 'master'
                    base_dict = {"name": program_name, "faculty": faculty, "cycle": cycle}
                    yield response.follow(
                        programs_link,
                        self.parse_program,
                        cb_kwargs={'base_dict': base_dict}
                    )

    @staticmethod
    def parse_program(response, base_dict):
        codes = u.cleanup(response.xpath("//div[@id='cycle']//tr//td[@class='code']").getall())
        # links = u.cleanup(response.xpath("//tr//td[@class='name']/a/@href").getall()
        # Programs can be divided in 3, 2 or 1 blocks (or there is no ects)
        nb_blocks = 3
        ects = u.cleanup(response.xpath("//div[@id='cycle']//tr[not(@class='title')]"
                                        "//td[@class='credit three-column']").getall())
        if len(ects) == 0:
            nb_blocks = 2
            ects = u.cleanup(response.xpath("//div[@id='cycle']//tr[not(@class='title')]"
                                            "//td[@class='credit two-column']").getall())
        if len(ects) == 0:
            nb_blocks = 1
            ects = u.cleanup(response.xpath("//div[@id='cycle']//tr[not(@class='title')]"
                                            "//td[@class='credit one-column']").getall())
        ects_slimmed = ects
        if nb_blocks > 1:
            ects_slimmed = []
            # ects are given for each block -> keep only one value
            for i in range(len(codes)):
                course_ects = [ects[i * 3], ects[i * 3 + 1],
                               ects[i * 3 + 2]] if nb_blocks == 3 else [ects[i * 2],
                                                                        ects[i * 2 + 1]]
                course_ects = [e for e in course_ects if len(e)]
                # If there is still a different number of ects only keep the first one
                ects_slimmed += [list(set(course_ects))[0]]

        cur_dict = {'campus': 'Namur',  # TODO: I think the campus is always Namur but to be checked
                    'id': '',  # Programs do not seem to have an id
                    'courses': codes,
                    'ects': ects_slimmed  # ,
                    # 'coursesnb': len(codes),
                    # 'ectsnb': len(ects_slimmed)
                    }

        yield {**base_dict, **cur_dict}


def get_programs(output):
    # Get list of programs using scrappy
    if os.path.exists(output):
        os.remove(output)
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'FEED_FORMAT': 'json',
        'FEED_URI': output
    })
    process.crawl(UNamurProgramSpider)
    process.start()  # the script will block here until the crawling is finished


if __name__ == '__main__':
    output_ = f"../../data/crawling-output/unamur_programs_{YEAR}.json"
    get_programs(output_)
