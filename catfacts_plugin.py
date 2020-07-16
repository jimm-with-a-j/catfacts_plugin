import requests
from ruxit.api.base_plugin import RemoteBasePlugin
import json
import logging
from pathlib import Path
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

class CatfactsPluginRemote(RemoteBasePlugin):
    def initialize(self, **kwargs):
        logger.info("Config: %s", self.config)
        self.dashboardname = self.config["dashboardname"]
        self.environmenturl = self.config["environmenturl"]
        self.dashboard_endpoint = self.environmenturl + "/api/config/v1/dashboards"
        self.token  = self.config["token"]
        self.auth_headers = {'Authorization': 'Api-Token ' + self.token, 'Content-Type': 'application/json'}
        self.validateSSL = self.config["validateSSL"]

    def query(self, **kwargs):
        self.create_or_update_dashboard()

        # reset lru cache so we catch any changes that have been  made between runs
        self.check_for_existing_dashboard.cache_clear()

    def get_fact(self):
        response = requests.get('https://catfact.ninja/facts')
        if response.status_code == 200:
            fact = response.json()['data'][0]['fact']
        else:
            fact = "Cat fact service unavailable :("
        return fact

    def create_or_update_dashboard(self):
        dashboard_json = self.generate_dashboard_json()
        existing_dashboard_id = self.check_for_existing_dashboard()
        if existing_dashboard_id == "":
            response = requests.post(self.dashboard_endpoint,
                                     headers=self.auth_headers,
                                     json=dashboard_json,
                                     verify=self.validateSSL)
        else:
            response = requests.put(self.dashboard_endpoint + '/' + existing_dashboard_id,
                                    headers=self.auth_headers,
                                    json=dashboard_json,
                                    verify=self.validateSSL)
        logger.info("Dashboard API call response code: " + str(response.status_code))

    def generate_dashboard_json(self):
        logger.info("Current directory: " + os.getcwd())
        template_location = Path(__file__).absolute().parent / 'dashboard_template.json'
        template_file = open(template_location, "r")
        dashboard_json = json.load(template_file)
        template_file.close()
        dashboard_json["dashboardMetadata"]["name"] = self.dashboardname

        #Update fact
        for tile in dashboard_json["tiles"]:
            if tile["name"] == "Fact":
                tile["markdown"] = self.get_fact()
                break

        existing_dashboard_id = self.check_for_existing_dashboard()
        if existing_dashboard_id != "":
            dashboard_json['id'] = existing_dashboard_id

        return dashboard_json

    # using lru cache to avoid making multiple calls per execution
    @lru_cache(maxsize=1)
    def check_for_existing_dashboard(self):
        # Check if dashboard already exists (by name) - empty string returned if no match
        existing_dash_id = ""
        response = requests.get(self.dashboard_endpoint, headers=self.auth_headers, verify=self.validateSSL)
        if response.status_code == 200:
            for dashboard in response.json()['dashboards']:
                if dashboard['name'] == self.dashboardname:
                    existing_dash_id = dashboard["id"]
        logger.info("Existing dash id: " + existing_dash_id)
        return existing_dash_id


