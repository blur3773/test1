

from app import create_app
from config import config

app = create_app()

if __name__ == '__main__':
    env = app.config.get('ENV', 'development')
    app_config = config.get(env, config['default'])

    host = getattr(app_config, 'HOST', '0.0.0.0')
    port = getattr(app_config, 'PORT', 5001)
    debug = getattr(app_config, 'DEBUG', False)

    app.run(host=host, port=port, debug=debug)
