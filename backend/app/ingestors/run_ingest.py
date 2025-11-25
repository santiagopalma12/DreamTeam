import argparse
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from app.ingestors.github_ingestor import ingest_commit
from app.ingestors.jira_ingestor import ingest_ticket
from app.ingestors.availability_ingestor import ingest_availability

def run_github(args):
    print("Running GitHub ingestion...")
    # In a real scenario, this would fetch from a queue or list of repos
    # For MVP/Demo, we ingest a specific commit or repo provided in args
    if args.commit and args.repo and args.author:
        ingest_commit(args.repo, args.commit, args.author)
        print(f"Ingested commit {args.commit}")
    else:
        print("For manual GitHub run, provide --repo, --commit, --author")

def run_jira(args):
    print("Running Jira ingestion...")
    if args.ticket:
        ingest_ticket(args.ticket)
        print(f"Ingested ticket {args.ticket}")
    else:
        print("For manual Jira run, provide --ticket")

def run_availability(args):
    print("Running Availability ingestion...")
    csv_path = args.csv or os.path.join(os.path.dirname(__file__), 'availability.csv')
    ingest_availability(csv_path)

def main():
    parser = argparse.ArgumentParser(description="Project Chimera Ingestion Pipeline")
    subparsers = parser.add_subparsers(dest='source', help='Ingestion source')

    # GitHub
    gh_parser = subparsers.add_parser('github', help='Run GitHub ingestion')
    gh_parser.add_argument('--repo', help='Repository fullname (owner/repo)')
    gh_parser.add_argument('--commit', help='Commit SHA')
    gh_parser.add_argument('--author', help='Author Login')

    # Jira
    jira_parser = subparsers.add_parser('jira', help='Run Jira ingestion')
    jira_parser.add_argument('--ticket', help='Ticket Key (e.g. PROJ-123)')

    # Availability
    avail_parser = subparsers.add_parser('availability', help='Run Availability ingestion')
    avail_parser.add_argument('--csv', help='Path to CSV file')

    args = parser.parse_args()

    if args.source == 'github':
        run_github(args)
    elif args.source == 'jira':
        run_jira(args)
    elif args.source == 'availability':
        run_availability(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
