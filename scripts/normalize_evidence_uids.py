"""Normalize Evidence nodes by assigning deterministic `uid` values.

This script is safe to run in dry-run mode (default). When run with `--apply`, it will set missing `ev.uid`
to a deterministic value computed from `url|date|actor` using sha1.

Usage:
  python scripts/normalize_evidence_uids.py         # dry-run, prints proposed updates
  python scripts/normalize_evidence_uids.py --apply  # perform updates

Notes:
- The script will skip Evidence nodes that already have a uid.
- It will not delete or modify legacy r.evidencias. A follow-up cleanup PR should remove legacy props after verification.
"""
import argparse
from app.db import get_driver
from app.scoring import make_evidence_uid


def find_evidence_nodes(driver):
    q = """
    MATCH (ev:Evidence)
    RETURN ev.uid AS uid, ev.url AS url, ev.date AS date, ev.actor AS actor, id(ev) AS _id
    """
    with driver.session() as s:
        res = s.run(q)
        return [r.data() for r in res]


def set_uid(driver, internal_id, uid):
    q = "MATCH (ev) WHERE id(ev) = $id SET ev.uid = $uid RETURN ev"
    with driver.session() as s:
        s.run(q, id=internal_id, uid=uid)


def export_proposed_csv(proposed, path):
    import csv
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['internal_id', 'proposed_uid', 'url', 'date', 'actor'])
        for _id, uid, url, date_str, actor in proposed:
            w.writerow([_id, uid, url, date_str, actor])
    return path


def main(apply=False, export_csv=None, driver=None):
    driver = driver or get_driver()
    nodes = find_evidence_nodes(driver)
    proposed = []
    for n in nodes:
        if n.get('uid'):
            continue
        url = n.get('url')
        date_str = n.get('date')
        actor = n.get('actor')
        uid = make_evidence_uid(url, date_str, actor)
        proposed.append((n.get('_id'), uid, url, date_str, actor))

    if export_csv:
        export_proposed_csv(proposed, export_csv)
        print(f'Exported proposed uids to {export_csv} (total {len(proposed)})')

    if not proposed:
        print('No evidence nodes without uid found. Nothing to do.')
        return proposed

    print(f'Proposed updates for {len(proposed)} evidence nodes:')
    for _id, uid, url, date_str, actor in proposed:
        print(f' id={_id} -> uid={uid} url={url} date={date_str} actor={actor}')

    if apply:
        confirm = input('Apply these updates? type YES to continue: ')
        if confirm != 'YES':
            print('Aborted by user.')
            return proposed
        for _id, uid, *_ in proposed:
            set_uid(driver, _id, uid)
        print('Applied updates.')
        return proposed
    else:
        print('Dry-run mode (no changes). Run with --apply to persist uids.')
        return proposed


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true', help='Apply changes')
    p.add_argument('--export-csv', help='Optional path to export proposed uids as CSV')
    args = p.parse_args()
    main(apply=args.apply, export_csv=args.export_csv)
