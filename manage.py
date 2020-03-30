#!/usr/bin/env python3

from flask_script import Manager, Server

from project.app import AlertmanagerActions

app = AlertmanagerActions()

manager = Manager(app.app)
manager.add_command("runserver", Server(use_reloader=False))

if __name__ == '__main__':
    manager.run()
