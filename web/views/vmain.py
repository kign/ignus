import os, logging, random, sys, json, uuid
from datetime import datetime, timedelta, date as Date
from traceback import print_exception
from time import time

from flask import session as flsk_s, url_for, render_template, request, jsonify, redirect, g
from inetlab.auth.synlogin import MSLogin, GLogin
from lib.shared import ajax_exception

# app.add_url_rule('/', 'home', view_func=home.main, methods=['GET'])
def home() :
    user, err = login(reg=True, ajax=False, maintenance=False)
    host = request.headers.get('host') or 'HOST'

    if err :
        state = str(uuid.uuid4())
        flsk_s['state'] = state

        return render_template('home.html',
                               ms_auth_url=MSLogin.build_auth_url(
                                   authorized_url=url_for("authorized", _external=True),
                                   state=state),
                               redirect_succ=url_for('home'),
                               maintenance=g.maintenance,
                               title= f"[DEV] Welcome to {host}!" if g.is_dev else f"Welcome to {host}!",
                               google_client_id=GLogin.CLIENT_ID)

    elif g.maintenance and not user['priv'] :
        return render_template("notauth.html", content='site under maintenance')

    else :
        return render_template('user.html',
                           user=user,
                           show_date=show_date, show_time=show_time,
                           query=g.db.get_user_urls(user['uid']),
                           title=["Existing URL's"])

# app.add_url_rule('/<string:shid>', 'redirect', view_func=home.redirect, methods=['GET'])
def shid_redirect(shid) :
    user, err = login(reg=False, ajax=False)

    headers = {h.lower().replace('-','_'):v for h,v in request.headers.items()
                    if h.lower() in ['accept-language', 'host', 'sec-ch-ua',
        'user-agent', 'x-appengine-city', 'x-appengine-citylatlong', 'x-appengine-country',
        'x-appengine-region', 'x-appengine-user-ip']}
    if not err :
        headers['internal'] = True

    url = g.db.redirect(shid, headers)
    logging.info("%r => %r", shid, url)
    if url is None :
        return "No such redirect", 404
    elif url is False :
        return "redirect inactive", 410
    else :
        return redirect(url, code=301)


def about() :
    user, err = login(reg=False, ajax=False)

    return render_template('about.html',
                           user=user,
                           maintenance=g.maintenance,
                           about_page=True,
                           title=["About the service"],
                           environ=os.environ)

def ajax_verify_shid() :
    try :
        user, err = login(reg=False, ajax=True)
        if err: return err

        shid = request.args.get('shid')
        return jsonify({'is_valid' : g.db.verify_shid(shid)})

    except Exception as err :
        print_exception(*sys.exc_info())
        return ajax_exception(err)


chars = list(map(chr, list(range(48, 58)) + list(range(65,91)) + list(range(97,123))))
def ajax_url_add() :
    try :
        user, err = login(reg=True, ajax=True)
        if err: return err

        logging.info("ajax_url_add(): received %s",
                     ", ".join(f"{k}={v}" for k, v in request.values.items()))

        shid = request.values.get('shid', '').strip()
        url = request.values.get('url', '').strip()
        _expire = request.values.get('expire')
        if _expire and _expire != "custom" :
            if _expire == 'never' :
                expire = None
            else :
                try :
                    expire = Date.today() + timedelta(days=int(_expire))
                except ValueError as err :
                    return jsonify({'error' : f'Invalid value expire=<{_expire}>'})
        else :
            _expire = request.values.get('expire-custom')
            if not _expire :
                return jsonify({'error': "Missing expire"})
            try :
                expire = datetime.strptime(_expire,"%Y-%m-%d").date()
            except ValueError as err :
                return jsonify({'error': f'Invalid value expire-custom=<{_expire}>'})

        if shid == '' :
            for _try in range(10) :
                shid = ''.join([random.choice(chars) for _ in range(3)])
                if g.db.verify_shid(shid) :
                    break
            else :
                return jsonify({'error': 'Cannot find SHID'})
        elif not g.db.verify_shid(shid) :
            return jsonify({f'error': 'Invalid SHID=<{shid}>'})

        logging.info("Inserting %s => %s, expires %s", shid, url, expire)
        g.db.url_add(user['uid'], shid, url, expire)

        return jsonify({'ok' : 'ok'})

    except Exception as err :
        print_exception(*sys.exc_info())
        return ajax_exception(err)

def ajax_update_expire() :
    try :
        user, err = login(reg=False, ajax=True)
        if err : return err

        e = request.get_json()
        logging.info("ajax_update_expire(%s)", json.dumps(e))

        shid = e['shid']
        if not g.db.is_owner(user['uid'], shid) :
            return jsonify({'error': "Not authorised"})

        _expire = e['expire'].strip()
        if _expire.lower() == 'never':
            expire = None
        else :
            try :
                expire = datetime.strptime(_expire,"%Y-%m-%d").date()
            except ValueError as err :
                return jsonify({'error': f'Invalid value expire=<{_expire}>'})

        logging.info("Updating expire for %s to %s", shid, expire)
        g.db.shid_update_expire(shid, expire)

        return jsonify({'ok' : 'ok', 'expire' : show_date(expire)})

    except Exception as err :
        print_exception(*sys.exc_info())
        return ajax_exception(err)

def shid_view(shid) :
    from user_agents import parse as ua_parse
    import flag

    user, err = login(reg=False, ajax=False)
    if err: return err

    if not g.db.is_owner(user['uid'], shid):
        return render_template("notauth.html", content='Not authorised to access this page')

    visits = g.db.shid_log(shid)

    def disp_ua(ua_string) :
        from collections import namedtuple
        Na = namedtuple('Na', ['family', 'version_string'])
        if not ua_string :
            na = Na(family='N/A', version_string='N/A')
            return na, na
        ua = ua_parse(ua_string)
        return ua.browser, ua.os

    def dump(v) :
        print("v =", v)

    return render_template('shid.html',
                           user=user,
                           shid=shid,
                           visits=visits,
                           disp_ua=disp_ua,
                           flag=flag.flag,
                           dump=dump, # temp/dbg
                           show_date=show_date, show_time=show_time,
                           title=["View URL"])

def shid_remove() :
    user, err = login(reg=False, ajax=False)
    if err: return err

    logging.info("shid_remove(): received %s",
                     ", ".join(f"{k}={v}" for k, v in request.values.items()))

    shid = request.values.get('shid')

    logging.info("shid_remove(%r)", shid)

    if not g.db.is_owner(user['uid'], shid):
        return render_template("notauth.html", content='Not authorised to access this page')

    del_visits = g.db.shid_delete('shid')

    return render_template('post.html',
                           title="Removed",
                           content=f"Shortcut <b>{shid}</b> removed successfully, including {del_visits} visits",
                           delay=10,
                           url=url_for('home'))

def login(reg, ajax, maintenance=None) :
    if maintenance is None :
        maintenance = g.maintenance
    user = flsk_s.get('user')
    if user is None or user.get('uid') is None:
        return None, jsonify({'error': 'Not authorised'}) if ajax else redirect(url_for('home'), code=302)
    user['priv'] = user['uid'] in g.priv_users
    if reg :
        g.db.register(user)
    if maintenance and not user['priv'] :
        return None, jsonify({'error': 'site under maintenance'}) if ajax else \
            render_template("notauth.html", content='site under maintenance')
    if user['provider'] == 'microsoft' :
        user['picture'] = 'https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/microsoft.svg'
    return user, None

def show_date (x) :
    if isinstance(x, str) :
        x = datetime.strptime(x,"%Y-%m-%d").date()
    days = (x - Date.today()).days

    def sd(d) :
        years = d / 365
        if years > 2:
            return "%d years" % years
        months = d / 30
        if months > 2:
            return "%d months" % months
        return "%d days" % d

    if days > 0 :
        return "in " + sd(days)
    elif days < 0 :
        return sd(-days) + " ago"
    else :
        return "today"

def show_time(t, style) :
    if style == "diff" :
        secs = time() - t
        if secs < 60:
            return "a few seconds ago"
        mins = secs/60
        if mins < 60 :
            return f"{int(mins)} mins ago"
        hours = mins/60
        if hours < 24 :
            return f"{int(hours)} hours ago"
        days = hours/24
        if days < 30 :
            return f"{int(days)} days ago"
        months = days/30
        if months < 13 :
            return f"{int(months)} months ago"
        years = days/365.25
        return f"{int(years)} years ago"

    elif style == "abs" :
        return datetime.fromtimestamp(float(t)).strftime("%Y-%m-%d %H:%M:%S")
