# -*- coding: utf-8 -*-
"""
QA/QC CLI entry points.
"""
import click
import logging
import os
import pprint
from rex.utilities.cli_dtypes import STR, STRLIST, INT
from rex.utilities.execution import SLURM
from rex.utilities.loggers import init_logger, init_mult

from reV.config.qa_qc_config import QaQcConfig
from reV.pipeline.status import Status
from reV.qa_qc.qa_qc import QaQc
from reV.qa_qc.summary import Summarize, SummaryPlots

logger = logging.getLogger(__name__)


@click.group()
@click.option('--name', '-n', default='reV-QA_QC', type=STR,
              help='reV QA/QC name, by default "reV-QA/QC".')
@click.option('-v', '--verbose', is_flag=True,
              help='Flag to turn on debug logging. Default is not verbose.')
@click.pass_context
def main(ctx, name, verbose):
    """reV QA/QC Command Line Interface"""
    ctx.ensure_object(dict)
    ctx.obj['NAME'] = name
    ctx.obj['VERBOSE'] = verbose


@main.group(chain=True)
@click.option('--out_dir', '-o', type=click.Path(), requried=True,
              help="Directory path to save summary tables and plots too")
@click.option('--log_file', '-log', type=click.Path(), default=None,
              help='File to log to, by default None')
@click.option('-v', '--verbose', is_flag=True,
              help='Flag to turn on debug logging.')
@click.pass_context
def summarize(ctx, out_dir, log_file, verbose):
    """
    Summarize reV data
    """
    ctx.obj['OUT_DIR'] = out_dir
    if any([verbose, ctx.obj['VERBOSE']]):
        log_level = 'DEBUG'
    else:
        log_level = 'INFO'

    ctx.obj['LOGGER'] = init_logger('reV.qa_qc', log_file=log_file,
                                    log_level=log_level)


@summarize.command()
@click.option('--h5_file', '-h5', type=click.Path(exists=True), required=True,
              help='Path to .h5 file to summarize')
@click.option('--dsets', '-ds', type=STRLIST, default=None,
              help='Datasets to summarize, by default None')
@click.option('--group', '-grp', type=STR, default=None,
              help=('Group within h5_file to summarize datasets for, by '
                    'default None'))
@click.option('--process_size', '-ps', type=INT, default=None,
              help='Number of sites to process at a time, by default None')
@click.option('--max_workers', '-w', type=INT, default=None,
              help=('Number of workers to use when summarizing 2D datasets,'
                    ' by default None'))
@click.pass_context
def h5(ctx, h5_file, dsets, group, process_size, max_workers):
    """
    Summarize datasets in .h5 file
    """
    Summarize.run(h5_file, ctx.obj['OUT_DIR'], group=group, dsets=dsets,
                  process_size=process_size, max_workers=max_workers)


@summarize.command()
@click.option('--plot_type', '-plt', default='plotly',
              type=click.Choice(['plot', 'plotly'], case_sensitive=False),
              help=(" plot_type of plot to create 'plot' or 'plotly', by "
                    "default 'plot'"))
@click.option('--cmap', '-cmap', type=str, default='viridis',
              help="Colormap name, by default 'viridis'")
@click.pass_context
def scatter_plots(ctx, plot_type, cmap):
    """
    create scatter plots from h5 summary tables
    """
    QaQc._scatter_plots(ctx.obj['OUT_DIR'], plot_type, cmap)


@summarize.command()
@click.option('--sc_table', '-sct', type=click.Path(exists=True),
              required=True, help='Path to .csv containing Supply Curve table')
@click.option('--columns', '-cols', type=STRLIST, default=None,
              help=('Column(s) to summarize, if None summarize all numeric '
                    'columns, by default None'))
@click.pass_context
def supply_curve_table(ctx, sc_table, columns):
    """
    Summarize Supply Curve Table
    """
    ctx.obj['SC_TABLE'] = sc_table
    Summarize.supply_curve(sc_table, ctx.obj['OUT_DIR'], columns=columns)


@summarize.command()
@click.option('--sc_table', '-sct', type=click.Path(exists=True), default=None,
              help=("Path to .csv containing Supply Curve table, can be "
                    "supplied in 'supply-curve-table'"))
@click.option('--plot_type', '-plt', default='plotly',
              type=click.Choice(['plot', 'plotly'], case_sensitive=False),
              help=(" plot_type of plot to create 'plot' or 'plotly', by "
                    "default 'plot'"))
@click.option('--lcoe', '-lcoe', type=STR, default='mean_lcoe',
              help="LCOE value to plot, by default 'mean_lcoe'")
@click.pass_context
def supply_curve_plot(ctx, sc_table, plot_type, lcoe):
    """
    Plot Supply Curve (cumulative capacity vs LCOE)
    """
    if sc_table is None:
        sc_table = ctx.obj['SC_TABLE']

    SummaryPlots.supply_curve(sc_table, ctx.obj['OUT_DIR'],
                              plot_type=plot_type, lcoe=lcoe)


@main.command()
@click.option('--h5_file', '-h5', type=click.Path(exists=True), required=True,
              help='Path to .h5 file to summarize')
@click.option('--out_dir', '-o', type=click.Path(), requried=True,
              help="Directory path to save summary tables and plots too")
@click.option('--dsets', '-ds', type=STRLIST, default=None,
              help='Datasets to summarize, by default None')
@click.option('--group', '-grp', type=STR, default=None,
              help=('Group within h5_file to summarize datasets for, by '
                    'default None'))
@click.option('--process_size', '-ps', type=INT, default=None,
              help='Number of sites to process at a time, by default None')
@click.option('--max_workers', '-w', type=INT, default=None,
              help=('Number of workers to use when summarizing 2D datasets,'
                    ' by default None'))
@click.option('--plot_type', '-plt', default='plotly',
              type=click.Choice(['plot', 'plotly'], case_sensitive=False),
              help=(" plot_type of plot to create 'plot' or 'plotly', by "
                    "default 'plot'"))
@click.option('--cmap', '-cmap', type=str, default='viridis',
              help="Colormap name, by default 'viridis'")
@click.option('--log_file', '-log', type=click.Path(), default=None,
              help='File to log to, by default None')
@click.option('-v', '--verbose', is_flag=True,
              help='Flag to turn on debug logging.')
@click.pass_context
def reV_h5(ctx, h5_file, out_dir, dsets, group, process_size, max_workers,
           plot_type, cmap, log_file, verbose):
    """
    Summarize and plot data for reV h5_file
    """
    if any([verbose, ctx.obj['VERBOSE']]):
        log_level = 'DEBUG'
    else:
        log_level = 'INFO'

    init_logger('reV.qa_qc', log_file=log_file, log_level=log_level)

    QaQc.run(h5_file, out_dir, dsets=dsets, group=group,
             process_size=process_size, max_workers=max_workers,
             plot_type=plot_type, cmap=cmap)


@main.command()
@click.option('--sc_table', '-sct', type=click.Path(exists=True),
              required=True, help='Path to .csv containing Supply Curve table')
@click.option('--out_dir', '-o', type=click.Path(), requried=True,
              help="Directory path to save summary tables and plots too")
@click.option('--columns', '-cols', type=STRLIST, default=None,
              help=('Column(s) to summarize, if None summarize all numeric '
                    'columns, by default None'))
@click.option('--plot_type', '-plt', default='plotly',
              type=click.Choice(['plot', 'plotly'], case_sensitive=False),
              help=(" plot_type of plot to create 'plot' or 'plotly', by "
                    "default 'plot'"))
@click.option('--lcoe', '-lcoe', type=STR, default='mean_lcoe',
              help="LCOE value to plot, by default 'mean_lcoe'")
@click.option('--log_file', '-log', type=click.Path(), default=None,
              help='File to log to, by default None')
@click.option('-v', '--verbose', is_flag=True,
              help='Flag to turn on debug logging.')
@click.pass_context
def supply_curve(ctx, sc_table, out_dir, columns, plot_type, lcoe, log_file,
                 verbose):
    """
    Summarize and plot reV Supply Curve dataß
    """
    if any([verbose, ctx.obj['VERBOSE']]):
        log_level = 'DEBUG'
    else:
        log_level = 'INFO'

    init_logger('reV.qa_qc', log_file=log_file, log_level=log_level)

    QaQc.supply_curve(sc_table, out_dir, columns=columns, lcoe=lcoe,
                      plot_type=plot_type)


@main.command()
@click.option('--config_file', '-c', required=True,
              type=click.Path(exists=True),
              help='reV QA/QC configuration json file.')
@click.option('-v', '--verbose', is_flag=True,
              help='Flag to turn on debug logging. Default is not verbose.')
@click.pass_context
def from_config(ctx, config_file, verbose):
    """Run reV QA/QC from a config file."""
    name = ctx.obj['NAME']

    # Instantiate the config object
    config = QaQcConfig(config_file)

    # take name from config if not default
    if config.name.lower() != 'rev':
        name = config.name

    ctx.obj['NAME'] = name

    # Enforce verbosity if logging level is specified in the config
    if config.log_level == logging.DEBUG:
        verbose = True

    # initialize loggers
    init_mult(name, config.logdir, modules=[__name__, 'reV.config',
                                            'reV.utilities', 'reV.qa_qc'],
              verbose=verbose)

    # Initial log statements
    logger.info('Running reV supply curve from config '
                'file: "{}"'.format(config_file))
    logger.info('Target output directory: "{}"'.format(config.dirout))
    logger.info('Target logging directory: "{}"'.format(config.logdir))
    logger.debug('The full configuration input is as follows:\n{}'
                 .format(pprint.pformat(config, indent=4)))

    if config.execution_control.option == 'local':
        status = Status.retrieve_job_status(config.dirout, 'QA-QC',
                                            name)
        if status != 'successful':
            Status.add_job(
                config.dirout, 'QA-QC', name, replace=True,
                job_attrs={'hardware': 'local',
                           'dirout': config.dirout})

            for module in config.module_names:
                module_config = config.get_module_inputs(module)
                fpath = module_config.fpath
                if fpath.endswith('.h5'):
                    log_file = os.path.join(
                        config.logdir,
                        os.path.basename(fpath).replace('.h5', '.log'))
                    ctx.invoke(reV_h5,
                               h5_file=fpath,
                               out_dir=module_config.out_dir,
                               dsets=module_config.dsets,
                               group=module_config.group,
                               process_size=module_config.process_size,
                               max_workers=module_config.max_workers,
                               plot_type=module_config.plot_type,
                               cmap=module_config.cmap,
                               log_file=log_file,
                               verbose=verbose)
                elif fpath.endswith('.csv'):
                    log_file = os.path.join(
                        config.logdir,
                        os.path.basename(fpath).replace('.csv', '.log'))
                    ctx.invoke(supply_curve,
                               sc_table=fpath,
                               out_dir=module_config.out_dir,
                               columns=module_config.columns,
                               plot_type=module_config.plot_type,
                               lcoe=module_config.lcoe,
                               log_file=log_file,
                               verbose=verbose)
                else:
                    msg = ("Cannot run QA/QC for {}: 'fpath' must be a '*.h5' "
                           "or '*.csv' reV output file, but {} was given!"
                           .format(module, fpath))
                    logger.error(msg)
                    raise ValueError(msg)

    elif config.execution_control.option in ('eagle', 'slurm'):
        launch_slurm(config)


def get_h5_cmd(name, h5_file, out_dir, dsets, group, process_size, max_workers,
               plot_type, cmap, log_file, verbose):
    """Build CLI call for reV_h5."""

    args = ('-h5 {h5_file} '
            '-o {out_dir} '
            '-ds {dsets} '
            '-grp {group} '
            '-ps {process_size} '
            '-w {max_workers} '
            '-plt {plot_type} '
            '-cmap {cmap} '
            '-log {log_file}'
            )

    args = args.format(h5_file=SLURM.s(h5_file),
                       out_dir=SLURM.s(out_dir),
                       dsets=SLURM.s(dsets),
                       group=SLURM.s(group),
                       process_size=SLURM.s(process_size),
                       max_workers=SLURM.s(max_workers),
                       plot_type=SLURM.s(plot_type),
                       cmap=SLURM.s(cmap),
                       log_file=SLURM.s(log_file),
                       )

    if verbose:
        args += '-v '

    cmd = ('python -m reV.qa_qc.cli_qa_qc -n {} reV-h5 {}'
           .format(SLURM.s(name), args))

    return cmd


def get_sc_cmd(name, sc_table, out_dir, columns, plot_type, lcoe, log_file,
               verbose):
    """Build CLI call for supply_curve."""

    args = ('-sct {sc_table} '
            '-o {out_dir} '
            '-cols {columns} '
            '-plt {plot_type} '
            '-lcoe {lcoe} '
            '-log {log_file}'
            )

    args = args.format(sc_table=SLURM.s(sc_table),
                       out_dir=SLURM.s(out_dir),
                       columns=SLURM.s(columns),
                       plot_type=SLURM.s(plot_type),
                       lcoe=SLURM.s(lcoe),
                       log_file=SLURM.s(log_file),
                       )

    if verbose:
        args += '-v '

    cmd = ('python -m reV.qa_qc.cli_qa_qc -n {} supply-curve {}'
           .format(SLURM.s(name), args))

    return cmd


def launch_slurm(config):
    """
    Launch slurm QA/QC job

    Parameters
    ----------
    config : dict
        'reV QA/QC configuration dictionary'
    """
    if config.log_level == logging.DEBUG:
        verbose = True

    out_dir = config.dirout

    node_cmd = []
    for module in config.module_names:
        module_config = config.get_module_inputs(module)
        fpath = module_config.fpath
        if fpath.endswith('.h5'):
            log_file = os.path.join(
                config.logdir,
                os.path.basename(fpath).replace('.h5', '.log'))
            node_cmd.append(get_h5_cmd(config.name, fpath,
                                       module_config.out_dir,
                                       module_config.dsets,
                                       module_config.group,
                                       module_config.process_size,
                                       module_config.max_workers,
                                       module_config.plot_type,
                                       module_config.cmap,
                                       log_file,
                                       verbose))
        elif fpath.endswith('.csv'):
            log_file = os.path.join(
                config.logdir,
                os.path.basename(fpath).replace('.csv', '.log'))
            node_cmd.append(get_sc_cmd(config.name, fpath,
                                       module_config.out_dir,
                                       module_config.columns,
                                       module_config.plot_type,
                                       module_config.lcoe,
                                       log_file,
                                       verbose))
        else:
            msg = ("Cannot run QA/QC for {}: 'fpath' must be a '*.h5' "
                   "or '*.csv' reV output file, but {} was given!"
                   .format(module, fpath))
            logger.error(msg)
            raise ValueError(msg)

    status = Status.retrieve_job_status(out_dir, 'QA-QC', config.name)
    if status == 'successful':
        msg = ('Job "{}" is successful in status json found in "{}", '
               'not re-running.'
               .format(config.name, out_dir))
    else:
        node_cmd = '\n'.join(node_cmd)
        logger.info('Running reV SC aggregation on SLURM with '
                    'node name "{}"'.format(config.name))
        slurm = SLURM(node_cmd, alloc=config.execution_control.alloc,
                      memory=config.execution_control.node_mem,
                      feature=config.execution_control.feature,
                      walltime=config.execution_control.walltime,
                      conda_env=config.execution_control.conda_env,
                      module=config.execution_control.module)
        if slurm.id:
            msg = ('Kicked off reV SC aggregation job "{}" '
                   '(SLURM jobid #{}).'
                   .format(config.name, slurm.id))
            Status.add_job(
                out_dir, 'supply-curve-aggregation', config.name, replace=True,
                job_attrs={'job_id': slurm.id, 'hardware': 'eagle',
                           'dirout': out_dir})
        else:
            msg = ('Was unable to kick off reV SC job "{}". '
                   'Please see the stdout error messages'
                   .format(config.name))

    click.echo(msg)
    logger.info(msg)


if __name__ == '__main__':
    main(obj={})
