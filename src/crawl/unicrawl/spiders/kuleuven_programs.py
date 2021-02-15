from abc import ABC

import scrapy

from config.settings import YEAR

BASE_URL = 'https://onderwijsaanbod.kuleuven.be/opleidingen/n/'


class KULeuvenProgramSpider(scrapy.Spider, ABC):
    name = 'kuleuven-programs'
    custom_settings = {
        'FEED_URI': f'../../data/crawling-output/kuleuven_programs_{YEAR}.json',
    }

    def start_requests(self):
        yield scrapy.Request(BASE_URL, self.parse_main)

    def parse_main(self, response):

        # 'Faculties'
        faculties = response.xpath("//h3/a/text()").getall()

        # Get program groups for each faculty
        for faculty in faculties:
            program_group_links = response.xpath(f"//h3/a[text()='{faculty}']/following::div[1]"
                                                 f"//li[contains(@class, 'taal_n') or "
                                                 f"contains(@class, 'taal_e')]/a/@href").getall()
            for link in program_group_links:
                base_dict = {"faculty": faculty}
                yield response.follow(link, self.parse_program_group, cb_kwargs={"base_dict": base_dict})

    def parse_program_group(self, response, base_dict):

        links = response.xpath("//div[@id='oase_heading_programmas']//li[@class='active']/a/@href").getall()
        codes = [link.split('.')[0] for link in links]

        for code, link in zip(codes, links):
            cur_dict = {"id": code}
            yield response.follow(link, self.parse_program, cb_kwargs={"base_dict": {**cur_dict, **base_dict}})

    @staticmethod
    def parse_program(response, base_dict):

        program_name = response.xpath("//h1/text()").get()
        campus = ''
        if '(' in program_name:
            campus = program_name.split('(')[-1].split(')')[0]
        cycle = 'other'
        if 'bachelor' in program_name or 'Bachelor' in program_name:
            cycle = 'bac'
        elif 'postgraduaat' in program_name or 'Postgraduaat' in program_name:
            cycle = 'postgrad'
        elif 'graduaat' in program_name or 'Graduaat' in program_name:
            cycle = 'grad'
        elif 'master' in program_name or 'Master' in program_name:
            cycle = 'master'
        elif 'doctor' in program_name or 'Doctor' in program_name:
            cycle = 'doctor'

        courses = response.xpath("//tr[contains(@class, 'opo_row')]//td[@class='code']/text()").getall()
        # If there are no courses to crawl, discard the program
        if len(courses) == 0:
            return
        courses_url = response.xpath("//td[@class='opleidingsonderdeel']/a/@href").getall()
        courses_url = [c.split("/syllabi/")[1].split('.htm')[0] for c in courses_url]

        def convert_ects_str(ects_str: str):
            if ects_str == '':
                return None
            return float(ects_str) if '.' in ects_str else int(ects_str)
        ects = response.xpath("//tr[contains(@class, 'opo_row')]//td[@class='sp']/text()").getall()
        ects = [convert_ects_str(e.split(" ")[0]) for e in ects]

        # Get list of unique courses and ects
        courses, courses_url, ects = zip(*set(zip(courses, courses_url, ects)))

        cur_dict = {'name': program_name,
                    'cycle': cycle,
                    'campus': campus,
                    'courses': courses,
                    'ects': ects,
                    'courses_urls': courses_url}

        yield {**base_dict, **cur_dict}
