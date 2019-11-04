# -*- coding: utf-8 -*-
"""
reV representative profile config

Created on Mon Jan 28 11:43:27 2019

@author: gbuster
"""
import logging

from reV.utilities.exceptions import ConfigError, PipelineError
from reV.config.base_analysis_config import AnalysisConfig
from reV.pipeline.pipeline import Pipeline


logger = logging.getLogger(__name__)


class RepProfilesConfig(AnalysisConfig):
    """Representative Profiles config."""

    NAME = 'rep_profiles'
    REQUIREMENTS = ('fpath_gen', 'rev_summary', 'reg_cols')

    def __init__(self, config):
        """
        Parameters
        ----------
        config : str | dict
            File path to config json (str), serialized json object (str),
            or dictionary with pre-extracted config.
        """
        super().__init__(config)

        self._default_cf_dset = 'cf_profile'
        self._default_rep_method = 'meanoid'
        self._default_err_method = 'rmse'

        self._preflight()

    def _preflight(self):
        """Perform pre-flight checks on the rep profiles config inputs"""
        missing = []
        for req in self.REQUIREMENTS:
            if self.get(req, None) is None:
                missing.append(req)
        if any(missing):
            raise ConfigError('Rep profiles config missing the following '
                              'keys: {}'.format(missing))

    @property
    def fpath_gen(self):
        """Get the generation data filepath"""

        fpath = self['fpath_gen']

        if fpath == 'PIPELINE':
            target_modules = ['multi-year', 'collect', 'generation']
            for target_module in target_modules:
                try:
                    fpath = Pipeline.parse_previous(
                        self.dirout, 'rep-profiles', target='fpath',
                        target_module=target_module)[0]
                except KeyError:
                    pass
                else:
                    break

            if fpath == 'PIPELINE':
                raise PipelineError('Could not parse fpath_gen from previous '
                                    'pipeline jobs.')
            else:
                logger.info('Rep profiles using the following '
                            'pipeline input for fpath_gen: {}'.format(fpath))

        return fpath

    @property
    def cf_dset(self):
        """Get the capacity factor dataset to get gen profiles from"""
        return self.get('cf_dset', self._default_cf_dset)

    @property
    def analysis_years(self):
        """Get analysis years."""
        analysis_years = None
        if 'analysis_years' in self:
            analysis_years = self['analysis_years']
        return analysis_years

    @property
    def rev_summary(self):
        """Get the rev summary input arg."""

        fpath = self['rev_summary']

        if fpath == 'PIPELINE':
            target_modules = ['aggregation', 'supply-curve']
            for target_module in target_modules:
                try:
                    fpath = Pipeline.parse_previous(
                        self.dirout, 'rep-profiles', target='fpath',
                        target_module=target_module)[0]
                except KeyError:
                    pass
                else:
                    break

            if fpath == 'PIPELINE':
                raise PipelineError('Could not parse rev_summary from '
                                    'previous pipeline jobs.')
            else:
                logger.info('Rep profiles using the following '
                            'pipeline input for rev_summary: {}'.format(fpath))

        return fpath

    @property
    def reg_cols(self):
        """Get the region columns input arg."""
        reg_cols = self['reg_cols']
        if isinstance(reg_cols, str):
            reg_cols = [reg_cols]
        return reg_cols

    @property
    def rep_method(self):
        """Get the representative profile method"""
        return self.get('rep_method', self._default_rep_method)

    @property
    def err_method(self):
        """Get the representative profile error method"""
        return self.get('err_method', self._default_err_method)
