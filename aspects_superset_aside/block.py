# pyright: reportMissingImports=false

"""Xblock aside enabling OpenAI driven summaries."""

import logging

import pkg_resources
from django.template import Context, Template
from django.utils import translation
from web_fragments.fragment import Fragment
from xblock.core import XBlock, XBlockAside
from xblock.fields import Scope, String
from xblockutils.resources import ResourceLoader

from supersetapiclient.client import SupersetClient
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

summary_fragment = """
<div>&nbsp;</div>
<div id="superser-aside">
    <span>Total xAPI events: {{ total_events }}</span>
</div>
"""

logger = logging.getLogger(__name__)


def _render_summary(context):
    template = Template(summary_fragment)
    return template.render(Context(context))


class AspectsSupersetAside(XBlockAside):
    """
    XBlock aside that injects a superset dashboard for instructors.
    """

    def _get_block(self):
        """
        Get the block wrapped by this aside.
        """
        from xmodule.modulestore.django import modulestore  # pylint: disable=import-error, import-outside-toplevel

        return modulestore().get_item(self.scope_ids.usage_id.usage_key)

    @XBlockAside.aside_for("student_view")
    def student_view_aside(
        self, block, context=None
    ):  # pylint: disable=unused-argument
        """
        Render the aside contents for the student view.
        """
        fragment = Fragment("")

        superset_host = "http://superset:8088/"
        superset_username = "EaFN5GkRE7Kh"
        superset_password = "OtI2H42YRyAp5drmbxrtywfH"

        client = SupersetClient(
            host=superset_host,
            username=superset_username,
            password=superset_password,
        )

        # You can get data using a defined chart id
        response = client.session.get(url=superset_host + 'api/v1/chart/6/data', data={"force": "True"}).json()
        total_events = response["result"][0]["data"][0]["count"]

        query_raw_events = [
            {
                "time_range": "No filter",
                "granularity": "emission_time",
                "filters": [],
                "extras": {
                    "time_grain_sqla": "P1D",
                    "having": "",
                    "having_druid": [],
                    "where": "(object_id like '%video%')",
                },
                "applied_time_extras": {},
                "columns": ["verb_id", "course_id", "object_id", "actor_id", "event_id"],
                "orderby": [],
                "annotation_layers": [],
                "row_limit": 10000,
                "timeseries_limit": 0,
                "order_desc": True,
                "url_params": {},
                "custom_params": {},
                "custom_form_data": {},
                "post_processing": [],
            }
        ]

        query_metrics = [
            {
                "time_range": "No filter",
                "granularity": "emission_time",
                "filters": [],
                "extras": {
                    "time_grain_sqla": "P1D",
                    "having": "",
                    "having_druid": [],
                    "where": ""
                },
                "applied_time_extras": {},
                "columns": [],
                "metrics": ["count"],
                "annotation_layers": [],
                "timeseries_limit": 0,
                "order_desc": True,
                "url_params": {},
                "custom_params": {},
                "custom_form_data": {}
            }
        ]
        # Or you can send multiple queries at once for the same datasource (dataset)
        another_response = client.session.post(
            url=superset_host + 'api/v1/chart/data',
            json={
                # The datasource object can point to a table, just provide the ID.
                # Not sure what others are possible
                "datasource": {"id": 2, "type": "table"},
                "force": False, # this force the query to be executed even if cached
                "queries": query_raw_events + query_metrics,
                "result_format": "json",
                "result_type": "full",
            },
        ).json()

        for result in another_response["result"]:
            for data in result["data"]:
                print(data)

        fragment.add_content(
            _render_summary(
                {
                    "superset_host": superset_host,
                    "block_id": block.scope_ids.usage_id.block_id,
                    "block_type": block.scope_ids.usage_id.block_type,
                    "course_id": block.scope_ids.usage_id.course_key,
                    "total_events": total_events,
                }
            )
        )

        return fragment

    @classmethod
    def should_apply_to_block(cls, block):
        """
        Override base XBlockAside implementation.

        Indicates whether this aside should apply to a given block type, course, and user.
        """
        return True


class AspectsSupersetXblock(XBlock, AspectsSupersetAside):
    """
    XBlock that injects a superset dashboard for instructors.
    """

    display_name = String(
        display_name="Display Name", default="Superset", scope=Scope.settings
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, context=None):
        """
        Render the primary view of the SupersetXBlock, shown to students when viewing courses.
        """
        if context:
            pass  # TO-DO: do something based on the context.

        html = self.resource_string("static/html/superset_xblock.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/superset_xblock.css"))

        # Add i18n js
        statici18n_js_url = self._get_statici18n_js_url()
        if statici18n_js_url:
            frag.add_javascript_url(
                self.runtime.local_resource_url(self, statici18n_js_url)
            )

        frag.add_javascript(self.resource_string("static/js/src/superset_xblock.js"))
        frag.initialize_js("SupersetXBlock")
        return frag

    # def studio_view(self, _context=None):
    #    """
    #    The studio view of the LimeSurveyXBlock, shown to instructors.
    #    """
    #    html = self.resource_string("static/html/limesurvey_edit.html")
    #    frag = Fragment(
    #        html.format(
    #            access_key=self.access_key, survey_id=self.survey_id, display_name=self.display_name,
    #        ),
    #    )
    #    frag.add_css(self.resource_string("static/css/limesurvey.css"))#

    # Add i18n js
    #    statici18n_js_url = self._get_statici18n_js_url()
    #    if statici18n_js_url:
    #        frag.add_javascript_url(self.runtime.local_resource_url(self, statici18n_js_url))

    #    frag.add_javascript(self.resource_string("static/js/src/limesurveyEdit.js"))
    #    frag.initialize_js("LimeSurveyXBlock")
    #    return frag

    @XBlock.json_handler
    def studio_submit(self, data, suffix=""):  # pylint: disable=unused-argument
        """
        Call when submitting the form in Studio.
        """
        self.display_name = data.get("display_name")

        return {
            "result": "success",
        }

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """Return a canned scenario for display in the workbench."""
        return [
            (
                "LimeSurveyXBlock",
                """<limesurvey/>
             """,
            ),
            (
                "Multiple LimeSurveyXBlock",
                """<vertical_demo>
                <limesurvey/>
                <limesurvey/>
                <limesurvey/>
                </vertical_demo>
             """,
            ),
        ]

    @staticmethod
    def _get_statici18n_js_url():
        """
        Return the Javascript translation file for the currently selected language, if any.

        Defaults to English if available.
        """
        locale_code = translation.get_language()
        if locale_code is None:
            return None
        text_js = "public/js/translations/{locale_code}/text.js"
        lang_code = locale_code.split("-")[0]
        for code in (locale_code, lang_code, "en"):
            loader = ResourceLoader(__name__)
            if pkg_resources.resource_exists(
                loader.module_name, text_js.format(locale_code=code)
            ):
                return text_js.format(locale_code=code)
        return None

    @staticmethod
    def get_dummy():
        """
        Return dummy method to generate initial i18n.
        """
        return translation.gettext_noop("Dummy")
