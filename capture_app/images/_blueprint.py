from quart import Blueprint
from quart_trio import QuartTrio


class QuartTrioBlueprint(Blueprint):
    app: QuartTrio

    @property
    def nursery(self):
        return self.app.nursery

    def register(self, app: QuartTrio, options: dict):
        self.app = app
        super().register(app, options)


blueprint = QuartTrioBlueprint("images", __name__)
