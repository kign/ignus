from flask import render_template, g


def main() :
    name = g.db.collection('test').document('me').get().get('name')
    return render_template('home.html', name=name)
