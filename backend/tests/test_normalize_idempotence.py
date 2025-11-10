import os
from app.db import get_driver
from scripts.normalize_evidence_uids import set_uid, main


def create_test_evidence(driver, url, date_str, actor):
    q = """
    CREATE (ev:Evidence {url:$url, date:$date, actor:$actor})
    RETURN id(ev) AS _id
    """
    with driver.session() as s:
        r = s.run(q, url=url, date=date_str, actor=actor)
        return list(r)[0]['_id']


def delete_test_evidence(driver, url):
    q = "MATCH (ev:Evidence {url:$url}) DETACH DELETE ev"
    with driver.session() as s:
        s.run(q, url=url)


def test_normalize_idempotence_and_csv(tmp_path):
    driver = get_driver()
    # create two test evidence nodes
    url1 = 'test://normalize/1'
    url2 = 'test://normalize/2'
    try:
        id1 = create_test_evidence(driver, url1, '2025-01-01', 'alice')
        id2 = create_test_evidence(driver, url2, '2025-06-01', 'bob')

        csv_path = os.path.join(str(tmp_path), 'proposed.csv')
        proposed = main(apply=False, export_csv=csv_path, driver=driver)

        # ensure our nodes appear in the proposed list
        ids = {entry[0] for entry in proposed if entry[2] in (url1, url2)}
        assert id1 in ids and id2 in ids

        assert os.path.exists(csv_path)
        with open(csv_path, 'r', encoding='utf-8') as fh:
            content = fh.read()
            assert 'internal_id' in content
            assert url1 in content and url2 in content

        # apply uids using the helper function (simulating --apply)
        for entry in proposed:
            if entry[0] in (id1, id2):
                _id, uid = entry[0], entry[1]
                set_uid(driver, _id, uid)

        # now find again; these should no longer appear as missing uid
        proposed_after = main(apply=False, driver=driver)
        ids_after = {entry[0] for entry in proposed_after}
        assert id1 not in ids_after and id2 not in ids_after

        # idempotence: running set_uid again with same values should be safe (no errors)
        for entry in proposed:
            if entry[0] in (id1, id2):
                _id, uid = entry[0], entry[1]
                set_uid(driver, _id, uid)

    finally:
        # cleanup
        delete_test_evidence(driver, url1)
        delete_test_evidence(driver, url2)
