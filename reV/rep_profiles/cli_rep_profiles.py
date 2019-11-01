# -*- coding: utf-8 -*-
"""
reV Representative Profiles command line interface (cli).
"""
import os
import click
import logging
import pprint
import time

from reV.utilities.execution import SLURM
from reV.utilities.cli_dtypes import STR, INT, STRLIST
from reV.utilities.loggers import init_mult
from reV.config.rep_profiles_config import RepProfilesConfig
from reV.rep_profiles.rep_profiles import RepProfiles
from reV.pipeline.status import Status

logger = logging.getLogger(__name__)


@click.command()
@click.option('--config_file', '-c', required=True,
              type=click.Path(exists=True),
              help='reV representative profiles configuration json file.')
@click.option('-v', '--verbose', is_flag=True,
              help='Flag to turn on debug logging. Default is not verbose.')
@click.pass_context
def from_config(ctx, config_file, verbose):
    """Run reV representative profiles from a config file."""
    name = ctx.obj['NAME']

    # Instantiate the config object
    config = RepProfilesConfig(config_file)

    # take name from config if not default
    if config.name.lower() != 'rev':
        name = config.name

    # Enforce verbosity if logging level is specified in the config
    if config.logging_level == logging.DEBUG:
        verbose = True

    # initialize loggers
    init_mult(name, config.logdir, modules=[__name__, 'reV.config',
                                            'reV.utilities'],
              verbose=verbose)

    # Initial log statements
    logger.info('Running reV 2.0 representative profiles from config '
                'file: "{}"'.format(config_file))
    logger.info('Target output directory: "{}"'.format(config.dirout))
    logger.info('Target logging directory: "{}"'.format(config.logdir))
    logger.debug('The full configuration input is as follows:\n{}'
                 .format(pprint.pformat(config, indent=4)))

    if config.analysis_years is not None and '{}' in config.fpath_gen:
        fpaths = [config.fpath_gen.format(y) for y in config.analysis_years]
        names = [name + '_{}'.format(y) for y in config.analysis_years]
    else:
        fpaths = [config.fpath_gen]
        names = [name]

    for name, fpath_gen in zip(names, fpaths):

        if config.execution_control.option == 'local':
            status = Status.retrieve_job_status(config.dirout, 'rep_profiles',
                                                name)
            if status != 'successful':
                Status.add_job(
                    config.dirout, 'rep_profiles', name, replace=True,
                    job_attrs={'hardware': 'local',
                               'fout': '{}.h5'.format(name),
                               'dirout': config.dirout})
                ctx.invoke(main, name, fpath_gen, config.rev_summary,
                           config.reg_cols, config.rep_method,
                           config.err_method, config.dirout, config.logdir,
                           verbose)

        elif config.execution_control.option == 'eagle':
            ctx.obj['NAME'] = name
            ctx.obj['FPATH_GEN'] = fpath_gen
            ctx.obj['REV_SUMMARY'] = config.rev_summary
            ctx.obj['REG_COLS'] = config.reg_cols
            ctx.obj['REP_METHOD'] = config.rep_method
            ctx.obj['ERR_METHOD'] = config.err_method
            ctx.obj['OUT_DIR'] = config.dirout
            ctx.obj['LOG_DIR'] = config.logdir
            ctx.obj['VERBOSE'] = verbose

            ctx.invoke(eagle,
                       alloc=config.execution_control.alloc,
                       memory=config.execution_control.node_mem,
                       walltime=config.execution_control.walltime,
                       feature=config.execution_control.feature)


@click.group(invoke_without_command=True)
@click.option('--name', '-n', default='rep_profiles', type=STR,
              help='Job name. Default is "rep_profiles".')
@click.option('--fpath_gen', '-g', type=click.Path(exists=True), required=True,
              help='Filepath to reV gen file.')
@click.option('--rev_summary', '-r', type=click.Path(exists=True),
              required=True, help='Filepath to reV SC summary (agg) file.')
@click.option('--reg_cols', '-rc', type=STRLIST,
              help='List of column rev summary column labels to define '
              'regions to get rep profiles for.')
@click.option('--rep_method', '-rm', type=STR, default='meanoid',
              help='String identifier for representative method '
              '(e.g. meanoid, medianoid).')
@click.option('--err_method', '-em', type=STR, default='rmse',
              help='String identifier for error method '
              '(e.g. rmse, mae, mbe).')
@click.option('--out_dir', '-od', type=STR, default='./',
              help='Directory to save rep profile output h5.')
@click.option('--log_dir', '-ld', type=STR, default='./logs/',
              help='Directory to save rep profile logs.')
@click.option('-v', '--verbose', is_flag=True,
              help='Flag to turn on debug logging. Default is not verbose.')
@click.pass_context
def main(ctx, name, fpath_gen, rev_summary, reg_cols, rep_method, err_method,
         out_dir, log_dir, verbose):
    """reV representative profiles CLI."""

    ctx.ensure_object(dict)
    ctx.obj['NAME'] = name
    ctx.obj['FPATH_GEN'] = fpath_gen
    ctx.obj['REV_SUMMARY'] = rev_summary
    ctx.obj['REG_COLS'] = reg_cols
    ctx.obj['REP_METHOD'] = rep_method
    ctx.obj['ERR_METHOD'] = err_method
    ctx.obj['OUT_DIR'] = out_dir
    ctx.obj['LOG_DIR'] = log_dir
    ctx.obj['VERBOSE'] = verbose

    if ctx.invoked_subcommand is None:
        t0 = time.time()
        init_mult(name, log_dir, modules=[__name__, 'reV.rep_profiles'],
                  verbose=verbose)

        fn_out = '{}.h5'.format(name)
        fout = os.path.join(out_dir, fn_out)
        RepProfiles.run(fpath_gen, rev_summary, reg_cols,
                        rep_method=rep_method, err_method=err_method,
                        fout=fout)

        runtime = (time.time() - t0) / 60
        logger.info('reV representative profiles complete. '
                    'Time elapsed: {:.2f} min. Target output dir: {}'
                    .format(runtime, out_dir))

        status = {'dirout': out_dir, 'fout': fn_out,
                  'job_status': 'successful',
                  'runtime': runtime,
                  'finput': [fpath_gen, rev_summary]}
        Status.make_job_file(out_dir, 'rep_profiles', name, status)


def get_node_cmd(name, fpath_gen, rev_summary, reg_cols, rep_method,
                 err_method, out_dir, log_dir, verbose):
    """Get a CLI call command for the rep profiles cli."""

    args = ('-n {name} '
            '-g {fpath_gen} '
            '-r {rev_summary} '
            '-rc {reg_cols} '
            '-rm {rep_method} '
            '-em {err_method} '
            '-od {out_dir} '
            '-ld {log_dir} '
            )

    args = args.format(name=SLURM.s(name),
                       fpath_gen=SLURM.s(fpath_gen),
                       rev_summary=SLURM.s(rev_summary),
                       reg_cols=SLURM.s(reg_cols),
                       rep_method=SLURM.s(rep_method),
                       err_method=SLURM.s(err_method),
                       out_dir=SLURM.s(out_dir),
                       log_dir=SLURM.s(log_dir),
                       )

    if verbose:
        args += '-v '

    cmd = 'python -m reV.rep_profiles.cli_rep_profiles {}'.format(args)
    return cmd


@main.command()
@click.option('--alloc', '-a', required=True, type=STR,
              help='Eagle allocation account name.')
@click.option('--memory', '-mem', default=None, type=INT,
              help='Eagle node memory request in GB. Default is None')
@click.option('--walltime', '-wt', default=1.0, type=float,
              help='Eagle walltime request in hours. Default is 1.0')
@click.option('--feature', '-l', default=None, type=STR,
              help=('Additional flags for SLURM job. Format is "--qos=high" '
                    'or "--depend=[state:job_id]". Default is None.'))
@click.option('--stdout_path', '-sout', default=None, type=STR,
              help='Subprocess standard output path. Default is in out_dir.')
@click.pass_context
def eagle(ctx, alloc, memory, walltime, feature, stdout_path):
    """Eagle submission tool for reV representative profiles."""

    name = ctx.obj['NAME']
    fpath_gen = ctx.obj['FPATH_GEN']
    rev_summary = ctx.obj['REV_SUMMARY']
    reg_cols = ctx.obj['REG_COLS']
    rep_method = ctx.obj['REP_METHOD']
    err_method = ctx.obj['ERR_METHOD']
    out_dir = ctx.obj['OUT_DIR']
    log_dir = ctx.obj['LOG_DIR']
    verbose = ctx.obj['VERBOSE']

    if stdout_path is None:
        stdout_path = os.path.join(log_dir, 'stdout/')

    cmd = get_node_cmd(name, fpath_gen, rev_summary, reg_cols, rep_method,
                       err_method, out_dir, log_dir, verbose)

    status = Status.retrieve_job_status(out_dir, 'rep_profiles', name)
    if status == 'successful':
        msg = ('Job "{}" is successful in status json found in "{}", '
               'not re-running.'
               .format(name, out_dir))
    else:
        logger.info('Running reV SC rep profiles on Eagle with '
                    'node name "{}"'.format(name))
        slurm = SLURM(cmd, alloc=alloc, memory=memory,
                      walltime=walltime, feature=feature,
                      name=name, stdout_path=stdout_path)
        if slurm.id:
            msg = ('Kicked off reV rep profiles job "{}" '
                   '(SLURM jobid #{}) on Eagle.'
                   .format(name, slurm.id))
            Status.add_job(
                out_dir, 'rep_profiles', name, replace=True,
                job_attrs={'job_id': slurm.id, 'hardware': 'eagle',
                           'fout': '{}.h5'.format(name), 'dirout': out_dir})
        else:
            msg = ('Was unable to kick off reV rep profiles job "{}". '
                   'Please see the stdout error messages'
                   .format(name))
    click.echo(msg)
    logger.info(msg)


if __name__ == '__main__':
    try:
        main(obj={})
    except Exception:
        logger.exception('Error running reV rep profiles CLI.')
        raise
