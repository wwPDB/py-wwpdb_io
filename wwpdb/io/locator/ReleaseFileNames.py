##
# File:  ReleaseFileNames.py
# Date:  Nov-2019  J. Berrisford
#
# Updated:
#  15-Nov-2019 E. Peisach  Code cleanups
#
##
"""
Methods for finding file names for entries within the for_release area of ftp archive

In general the methods take accession and for_release flags.  for_release indicates the for_release directory.

"""


class ReleaseFileNames:
    def __init__(self):
        #                context   public    for_rel   gzip_pub, gzip_rel

        self.__mapping = {'model': ['{}.cif', '{}.cif', True, True],
                          'sf': ['r{}sf.ent.gz', '{}-sf.cif', False, True],
                          'cs': ['{}_cs.str', '{}_cs.str', True, False],
                          'emdxml': ['{}-v30.xml', '{}_v3.xml', False, False],
                          'emdmap': ['{}.map', '{}.map', True, True],
                          'emdfsc': ['{}_fsc.xml', '{}_fsc.xml', False, False],
                          'validpdf': ['{}_validation.pdf', '{}_validation.pdf', False, False],
                          'validpdffull': ['{}_full_validation.pdf', '{}_full_validation.pdf', False, False],
                          'validxml': ['{}_validation.xml', '{}_validation.xml', False, False],
                          'validpng': ['{}_multipercentile_validation.png', '{}_multipercentile_validation.png',
                                       False, False],
                          'validsvg': ['{}_multipercentile_validation.svg', '{}_multipercentile_validation.svg',
                                       False, False],
                          'valid2fo': ['{}_validation_2fo-fc_map_coef.cif', '{}_validation_2fo-fc_map_coef.cif',
                                       False, False],
                          'validfo': ['{}_validation_fo-fc_map_coef.cif', '{}_validation_fo-fc_map_coef.cif',
                                      False, False],
                          }

    def __add_gzip(self, filename, set_gzip=False):
        if set_gzip:
            self.__gzip = True
        self.__gzip = False
        if self.__gzip:
            return filename + ".gz"
        return filename

    def __getfname(self, content, accession, for_release):
        """Retrieves the released content file name with compression"""
        assert(content in self.__mapping)
        (public, release, pub_gzip, rel_gzip) = self.__mapping[content]
        if for_release:
            base = release
            gzipflag = rel_gzip
        else:
            base = public
            gzipflag = pub_gzip
        suffix = '.gz' if gzipflag else ''

        fname = base.format(accession) + suffix

        return fname

    def get_model(self, accession, for_release=False):
        return self.__getfname('model', accession, for_release)

    def get_structure_factor(self, accession, for_release=False):
        return self.__getfname('sf', accession, for_release)

    def get_chemical_shifts(self, accession, for_release=False):
        return self.__getfname('cs', accession, for_release)

    def get_emdb_xml(self, accession, for_release=False):
        return self.__getfname('emdxml', accession, for_release)

    def get_emdb_map(self, accession, for_release=False):
        return self.__getfname('emdmap', accession, for_release)

    def get_emdb_fsc(self, accession, for_release=False):
        return self.__getfname('emdfsc', accession, for_release)

    def get_validation_pdf(self, accession, for_release=False):
        return self.__getfname('validpdf', accession, for_release)

    def get_validation_full_pdf(self, accession, for_release=False):
        return self.__getfname('validpdffull', accession, for_release)

    def get_validation_xml(self, accession, for_release=False):
        return self.__getfname('validxml', accession, for_release)

    def get_validation_png(self, accession, for_release=False):
        return self.__getfname('validpng', accession, for_release)

    def get_validation_svg(self, accession, for_release=False):
        return self.__getfname('validsvg', accession, for_release)

    def get_2fofc(self, accession, for_release=False):
        return self.__getfname('valid2fo', accession, for_release)

    def get_fofc(self, accession, for_release=False):
        return self.__getfname('validfo', accession, for_release)


if __name__ == '__main__':
    rf = ReleaseFileNames()
    print("Pub model %s" % rf.get_model('1abc'))
    print("Rel model %s" % rf.get_model('1abc', True))
    print("Pub sf: %s" % rf.get_structure_factor('1abc'))
    print("Rel sf: %s" % rf.get_structure_factor('1abc', True))
    print("Pub cs: %s" % rf.get_chemical_shifts('1abc'))
    print("Rel cs: %s" % rf.get_chemical_shifts('1abc', True))
    print("Pub emdxml: %s" % rf.get_emdb_xml('EMD-1234'))
    print("Rel emdxml: %s" % rf.get_emdb_xml('EMD-1234', True))
    print("Pub emdmap: %s" % rf.get_emdb_map('EMD-1234'))
    print("Rel emdmap: %s" % rf.get_emdb_map('EMD-1234', True))
    print("Pub validpdf: %s" % rf.get_validation_pdf('1abc'))
    print("Rel validpdf: %s" % rf.get_validation_pdf('1abc', True))
    print("Pub validfullpdf: %s" % rf.get_validation_full_pdf('1abc'))
    print("Rel validfullpdf: %s" % rf.get_validation_full_pdf('1abc', True))
    print("Pub validxml: %s" % rf.get_validation_xml('1abc'))
    print("Rel validxml: %s" % rf.get_validation_xml('1abc', True))
    print("Pub validsvg: %s" % rf.get_validation_svg('1abc'))
    print("Rel validsvg: %s" % rf.get_validation_svg('1abc', True))
    print("Pub validpng: %s" % rf.get_validation_svg('1abc'))
    print("Rel validpng: %s" % rf.get_validation_svg('1abc', True))
    print("Pub 2fo-fc: %s" % rf.get_2fofc('1abc'))
    print("Rel 2fo-fc: %s" % rf.get_2fofc('1abc', True))
    print("Pub fo-fc: %s" % rf.get_fofc('1abc'))
    print("Rel fo-fc: %s" % rf.get_fofc('1abc', True))
