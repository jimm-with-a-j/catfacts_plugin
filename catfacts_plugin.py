import requests
from ruxit.api.base_plugin import RemoteBasePlugin
import json
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class CatfactsPluginRemote(RemoteBasePlugin):
    def initialize(self, **kwargs):
        logger.info("Config: %s", self.config)
        self.dashboardname = self.config["dashboardname"]
        self.environmenturl = self.config["environmenturl"]
        self.dashboard_endpoint = self.environmenturl + "/api/config/v1/dashboards"
        self.token  = self.config["token"]
        self.auth_headers = {'Authorization': 'Api-Token ' + self.token, 'Content-Type': 'application/json'}

    def query(self, **kwargs):
        self.create_or_update_dashboard()

    def get_fact(self):
        response = requests.get('https://catfact.ninja/facts')
        fact = response.json()['data'][0]['fact']
        return fact

    def create_or_update_dashboard(self):
        dashboard_json = self.generate_dashboard_json()
        existing_dashboard_id = self.check_for_existing_dashboard()
        if existing_dashboard_id == "":
            response = requests.post(self.dashboard_endpoint, headers=self.auth_headers, json=self.generate_dashboard_json())
        else:
            response = requests.put(self.dashboard_endpoint + '/' + existing_dashboard_id, headers=self.auth_headers, json=self.generate_dashboard_json())

    def generate_dashboard_json(self):
        logger.info("Current directory:" + os.getcwd())
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

    def check_for_existing_dashboard(self):
        # Check if dashboard already exists (by name) - empty string returned if no match
        existing_dash_id = ""
        response = requests.get(self.dashboard_endpoint, headers=self.auth_headers)
        if response.status_code == 200:
            for dashboard in response.json()['dashboards']:
                if dashboard['name'] == self.dashboardname:
                    existing_dash_id = dashboard["id"]

        return existing_dash_id


