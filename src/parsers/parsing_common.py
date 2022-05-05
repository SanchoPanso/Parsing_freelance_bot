import aiohttp
from abc import ABC, abstractmethod
from enum import Enum
from src.json_io import get_data_from_file, write_data_into_file
import time
import logging

logger = logging.getLogger("App.Parser")


class ParsingResult(Enum):
    SUCCESSFUL = 0
    FAILURE = 1
    BLOCKED_BY_GUARD = 2
    NOT_IMPLEMENTED = 3


class Parser(ABC):
    """
    Abstract class for another parsers
    """
    def __init__(self, projects_url: str, project_data_file_path: str):
        """Constructor"""
        self.timeout = aiohttp.ClientTimeout(total=30)          # timeout
        self.project_dict = dict()                              # temporary storage for parsed project from one page
        self.project_dict_from_file = dict()
        self.last_checking_time = None                          # last time when parsing occured
        self.max_time_lag = 5 * 60 * 60                         # max time lag (i haven't yet known how to describe)
        self.projects_url = projects_url                        # url of page with list of projects (orders)
        self.project_data_file_path = project_data_file_path    # file that contains all parsed projects
        self.end_point_is_not_reached = bool()                  # variable that shows when you need to stop parsing

    async def check_news(self) -> tuple:
        """
        Common method for checking news in the certain site
        :return: tuple of list with news and return code
        """
        logging.info('Checking news started')
        # create dict that is a copy of data in project_data_file
        self.project_dict_from_file = get_data_from_file('parsers\\project_data_dir\\project_data.json')
        # create empty list for found news
        news_list = []
        
        # some parsers use last_checking_time for define the end point
        # So there is last_checking_time initialization
        # if if is the first news checking then we suppose that last_checking_time was max_time_lag seconds ago
        current_time = time.time()
        if self.last_checking_time is None:
            self.last_checking_time = current_time - self.max_time_lag

        page_number = 1
        self.end_point_is_not_reached = True
        while self.end_point_is_not_reached:
            
            # parse one page with projects (result will be in self.project_dict)
            # If something went wrong, interrupt parsing
            result_code = await self.parse_single_page_with_projects(self.projects_url, page_number)
            if result_code != ParsingResult.SUCCESSFUL:
                if result_code == ParsingResult.NOT_IMPLEMENTED:
                    raise NotImplementedError
                else:
                    return news_list, result_code
            
            # update value of end_point_is_not_reached
            self.update_cond_for_cycle_ending()
            
            # in cycle if a project is valid and not in project_data_file then
            # add it to news_list and project_dict_from_file
            keys = self.project_dict.keys()
            for key in keys:
                if self.is_valid_project(self.project_dict[key]):
                    if key not in self.project_dict_from_file.keys():
                        news_list.append(self.format_new(self.project_dict[key]))
                        self.project_dict_from_file[key] = self.project_dict[key]
            
            # move on to the next page
            page_number += 1
        
        # if cycle is closed normally then last_checking time is corrent time
        self.last_checking_time = current_time

        # update data in project_dict_from_file
        write_data_into_file(self.project_dict_from_file, 'parsers\\project_data_dir\\project_data.json')

        # make project_dict empty for the next
        self.project_dict = dict()
        return news_list, ParsingResult.SUCCESSFUL

    @abstractmethod
    async def parse_single_page_with_projects(self, page_url, page_number) -> ParsingResult:
        """start parsing of single projects placed in the page"""
        pass

    @abstractmethod
    async def parse_single_project(self, project_url: str, project_mark: bool,
                                   session: aiohttp.ClientSession):
        """Take data from a single page with a project description."""
        pass

    @abstractmethod
    def update_cond_for_cycle_ending(self):
        """
        Update conditional variable (end_point_is_not_reached) to define
        when the parsing cycle must be stoped
        """

    @abstractmethod
    def is_valid_project(self, project_info: dict) -> bool:
        """check whether the project matches the required conditions"""

    @abstractmethod
    def format_new(self, new: dict) -> str:
        """Format a new from dict info to one string in order to send this string to users"""



