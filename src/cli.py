"""Command-line interface for Windows Error Analyzer."""

import sys

import click

from src.parsers.dump_parser import DumpParserError
from src.parsers.windbg_parser import WinDbgParserError
from src.parsers import get_parser_for
from src.reporters.console_reporter import ConsoleReporter


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Windows Error Analyzer - Extract and analyze Windows crash dumps and event logs."""
    pass


@cli.command()
@click.option(
    "--dmp",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to Windows dump file (.dmp)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def analyze(dmp, verbose):
    """Analyze Windows dump files and display crash information.
    
    This command extracts and displays information from Windows memory dump files,
    including crash details, error codes, stack traces, and system information.
    
    Example:
        windows-error-analyzer analyze --dmp crash.dmp
    """
    reporter = ConsoleReporter()
    
    if not dmp:
        reporter.print_error("At least one input file (--dmp) is required")
        sys.exit(1)
    
    try:
        if dmp:
            if verbose:
                reporter.print_info(f"Parsing dump file: {dmp}")
            
            parser = get_parser_for(dmp)
            analysis = parser.parse(dmp)
            
            if verbose:
                reporter.print_success("Dump file parsed successfully")
            
            reporter.display_dump_analysis(analysis)
            
            reporter.print_success("Analysis complete!")
            sys.exit(0)
            
    except FileNotFoundError as e:
        reporter.print_error(str(e))
        sys.exit(2)
    except DumpParserError as e:
        reporter.print_error(f"ダンプファイルの解析に失敗しました: {e}")
        sys.exit(3)
    except WinDbgParserError as e:
        reporter.print_error(f"WinDbgでの解析に失敗しました: {e}")
        reporter.print_info("Windows SDK Debugging Toolsがインストールされ、CDB_PATH/KD_PATHが正しく設定されているか確認してください")
        sys.exit(3)
    except Exception as e:
        reporter.print_error(f"予期しないエラーが発生しました: {e}")
        if verbose:
            reporter.console.print_exception()
        sys.exit(10)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
