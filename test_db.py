import MySQLdb
import urllib.parse
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[logging.FileHandler('railway_connection.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# URL de connexion Railway


try:
    # Extraire les composants de l'URL
    parsed = urllib.parse.urlparse(db_url)
    
    dbname = parsed.path.strip('/')
    username = parsed.username
    password = parsed.password
    hostname = parsed.hostname
    port = parsed.port
    
    logger.info(f"Tentative de connexion à {hostname}:{port}/{dbname} avec l'utilisateur {username}")
    
    # Tenter la connexion
    connection = MySQLdb.connect(
        host=hostname,
        user=username,
        passwd=password,
        db=dbname,
        port=port
    )
    
    logger.info("Connexion réussie!")
    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    logger.info(f"Version MySQL: {version[0]}")
    connection.close()
    
except Exception as e:
    logger.error(f"Erreur de connexion: {e}", exc_info=True)