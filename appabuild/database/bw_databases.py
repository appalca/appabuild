"""
This module contains classes and functions to interact with databases imported in
Brightway project.
"""
from __future__ import annotations

import re
from typing import List, Optional, Union

import brightway2 as bw
from pydantic import BaseModel

from appabuild.database.serialized_data import ActivityIdentifier
from appabuild.exceptions import BwDatabaseError


class BwDatabase(BaseModel):
    """
    Interacts with the database with corresponding name imported in Brightway project.
    """

    name: str

    @property
    def database(self):
        """
        Brightway database object
        :return:
        """
        return bw.Database(self.name)

    def search_activity(
        self, regexes: dict, must_find_only_one: Optional[bool] = False
    ) -> Union[ActivityIdentifier, List[ActivityIdentifier]]:
        """
        Search an activity in database with a set of regexes on any activities' field.
        :param regexes: key is the field and value the regex to match.
        :param must_find_only_one: if True, will raise an exception if the quantity of
        matching activities is different than one.
        :return: ActivityIdentifier, or list of ActivityIdentifier of matching
        activities.
        """
        matching_acts = []
        all_activities = [i for i in self.database]
        for field, regex in {k: v for k, v in regexes.items() if v is not None}.items():
            matching_acts.append(
                [i for i in all_activities if re.fullmatch(regex, i[field])]
            )
        matching_activities = list(set.intersection(*map(set, matching_acts)))
        if must_find_only_one and len(matching_activities) < 1:
            raise BwDatabaseError(
                f"Cannot find any activity resolving the following regexes: {regexes}."
            )
        if must_find_only_one and len(matching_activities) > 1:
            raise BwDatabaseError(
                f"Too many activity matching the following regexes {regexes}. Matches "
                f"are {matching_activities}."
            )
        if must_find_only_one:
            return ActivityIdentifier(
                database=matching_activities[0][0], uuid=matching_activities[0][1]
            )
        return [
            ActivityIdentifier(database=matching_activity[0], uuid=matching_activity[1])
            for matching_activity in matching_activities
        ]

    def resolve_activity_identifier(
        self, unresolved_activity_identifier: ActivityIdentifier
    ) -> ActivityIdentifier:
        """
        Resolve an unresolved activity identifier, i.e. find uuid of an activity
        identified by a set of regexes.
        Raise an error if more or less than one activity is found.
        :param unresolved_activity_identifier: activity identified by a set of
        regexes. Must be of the same database.
        :return: resolved ActivityIdentifier, i.e. with uuid defined.
        """
        regexes = unresolved_activity_identifier.model_dump()
        database = regexes.pop("database")
        if database != self.name:
            raise ValueError(
                f"Cannot search activity on a different database ({database} != "
                f"{self.name})."
            )
        activity_identifier = self.search_activity(
            regexes=regexes, must_find_only_one=True
        )
        return activity_identifier
