import unittest


## MARCHE PAS ENCORE

if __name__ == "__main__":
    # decouvrir et charger tous les tests du répertoire tests et ses sous dossiers
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir="./tests", pattern="test_*.py")
    print(test_suite)

    # exécuter tous les tests trouvés
    test_runner = unittest.TextTestRunner()
    test_runner.run(test_suite)


# python -m unittest .\tests\utilitaire\test_face_recognition_utils.py
# python -m unittest .\tests\utilitaire\test_face_data_utils.py

"""
=> Ajouter des data au fichier data_test.json (code à rajouter dans le main.py) :

import json

with open("./tests/Test_data/data_test.json", "w") as file: 
    json.dump({'face_db': face_db, 'existing_attendance': list(existing_attendance)}, file)
"""
