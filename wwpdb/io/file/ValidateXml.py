# ruff: noqa: T201,S408
##
# File:  ValidateXml.py
# Date:  14-Aug-2014
# Updates:
##
"""
Parse validation XML report

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2014 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import traceback
from typing import Dict, List, Literal, Optional, TextIO, Union, cast, overload
from xml.dom import minidom

from typing_extensions import TypedDict

# Need to add  plane-outlier all List[Dict[str, str]]
ValidateXmlOutliersKeys = Literal[
    "angle-outlier",
    "atom_inclusion_all_atoms",
    "atom_inclusion_backbone",
    "bond-outlier",
    "chain_average_residue_inclusion",
    "chiral-outlier",
    "clash",
    "dihedralangle_violation",
    "distance_violation",
    "ligand-rsrz-outlier",
    "mog-angle-outlier",
    "mog-bond-outlier",
    "mog-ring-outlier",
    "mog-torsion-outlier",
    "plane-outlier",
    "polymer-rsrz-outlier",
    "r_free_diff",
    "r_work_diff",
    "torsion-outlier",
]
ValidateXmlOutliers = TypedDict(
    "ValidateXmlOutliers",
    {
        "angle-outlier": List[Dict[str, str]],
        "atom_inclusion_all_atoms": str,
        "atom_inclusion_backbone": str,
        "bond-outlier": List[Dict[str, str]],
        "chain_average_residue_inclusion": List[Dict[str, Union[str, float]]],
        "chiral-outlier": List[Dict[str, str]],
        "clash": List[Dict[str, str]],
        "dihedralangle_violation": List[Dict[str, str]],
        "distance_violation": List[Dict[str, str]],
        "ligand-rsrz-outlier": List[Dict[str, str]],
        "mog-angle-outlier": List[Dict[str, str]],
        "mog-bond-outlier": List[Dict[str, str]],
        "mog-ring-outlier": List[Dict[str, str]],
        "mog-torsion-outlier": List[Dict[str, str]],
        "plane-outlier": List[Dict[str, str]],
        "polymer-rsrz-outlier": List[Dict[str, str]],
        "r_free_diff": List[Dict[str, str]],
        "r_work_diff": List[Dict[str, str]],
        "symm-clash": List[Dict[str, str]],
        "torsion-outlier": List[Dict[str, str]],
    },
    total=False,
)


class ValidateXml:
    """Class responsible for parsing validation XML report"""

    def __init__(self, FileName: Optional[str] = None, verbose: bool = False, log: TextIO = sys.stderr) -> None:  # noqa: ARG002 pylint: disable=unused-argument
        self.__xmlFile = FileName
        if self.__xmlFile is None:
            raise ValueError
        self.__doc = minidom.parse(self.__xmlFile)  # noqa: S318
        #
        self.clashMap: Dict[str, List[Dict[str, str]]] = {}
        self.clashOutliers: List[Dict[str, str]] = []
        self.summaryValues: Dict[str, float] = {}
        self.__outlierMap: Dict[str, List[str]] = {}
        # self.__outlierResult: Dict[str, str | List[str] | List[Dict[str, str]]] = {}
        self.__outlierResult: ValidateXmlOutliers = {}
        self.__calculated_completeness = ""
        self.__number_of_errors_while_mapping = 0
        self.__number_of_warnings_while_mapping = 0
        self.__not_found_in_structure_cs_list: List[List[str]] = []
        self.__not_found_residue_in_structure_cs_list: List[List[str]] = []
        self.__cs_outlier_list: List[List[str]] = []
        self.__cs_referencing_offset_list: List[List[str]] = []
        self.__has_cs_referencing_offset_flag = False
        #
        self.__getOutlierDefinition()
        self.__parse()

    @overload
    def getOutlier(self, Type: Literal["atom_inclusion_all_atoms", "atom_inclusion_backbone"]) -> str: ...

    @overload
    def getOutlier(self, Type: Literal["chain_average_residue_inclusion"]) -> List[Dict[str, Union[str, float]]]: ...

    @overload
    def getOutlier(
        self,
        Type: Literal[
            "angle-outlier",
            "bond-outlier",
            "chiral-outlier",
            "clash",
            "dihedralangle_violation",
            "distance_violation",
            "ligand-rsrz-outlier",
            "mog-angle-outlier",
            "mog-bond-outlier",
            "mog-ring-outlier",
            "mog-torsion-outlier",
            "plane-outlier",
            "polymer-rsrz-outlier",
            "r_free_diff",
            "r_work_diff",
            "torsion-outlier",
        ],
    ) -> List[Dict[str, str]]: ...

    def getOutlier(self, Type: ValidateXmlOutliersKeys) -> Union[str, List[dict[str, Union[str, float]]], List[Dict[str, str]]]:
        """"""
        if Type in self.__outlierResult:
            return self.__outlierResult[Type]
        #
        return []

    def getClashOutliers(self) -> List[Dict[str, str]]:
        """"""
        return self.clashOutliers

    def getCalculatedCompleteness(self) -> str:
        """"""
        return self.__calculated_completeness

    def getCsMappingErrorNumber(self) -> int:
        """"""
        return self.__number_of_errors_while_mapping

    def getCsMappingWarningNumber(self) -> int:
        """"""
        return self.__number_of_warnings_while_mapping

    def getNotFoundInStructureCsList(self) -> list[list[str]]:
        """"""
        return self.__not_found_in_structure_cs_list

    def getNotFoundResidueInStructureCsList(self) -> list[list[str]]:
        """"""
        return self.__not_found_residue_in_structure_cs_list

    def getCsOutliers(self) -> list[list[str]]:
        """"""
        return self.__cs_outlier_list

    def getCsReferencingOffsetFlag(self) -> bool:
        """"""
        return self.__has_cs_referencing_offset_flag

    def getSummary(self) -> dict[str, float]:
        return self.summaryValues

    def __getOutlierDefinition(self) -> None:
        """"""
        self.__outlierMap["torsion-outlier"] = ["phi", "psi"]
        self.__outlierMap["mog-ring-outlier"] = ["atoms", "mean", "mindiff", "stdev", "numobs"]
        self.__outlierMap["mog-angle-outlier"] = ["atoms", "mean", "mindiff", "stdev", "numobs", "Zscore", "obsval"]
        self.__outlierMap["mog-torsion-outlier"] = ["atoms", "mean", "mindiff", "stdev", "numobs", "obsval"]
        self.__outlierMap["mog-bond-outlier"] = ["atoms", "mean", "mindiff", "stdev", "numobs", "Zscore", "obsval"]
        self.__outlierMap["chiral-outlier"] = ["atom", "problem"]
        self.__outlierMap["plane-outlier"] = ["omega", "improper", "planeRMSD", "type"]
        self.__outlierMap["bond-outlier"] = ["atom0", "atom1", "mean", "stdev", "obs", "z", "link"]
        self.__outlierMap["angle-outlier"] = ["atom0", "atom1", "atom2", "mean", "stdev", "obs", "z", "link"]
        self.__outlierMap["clash"] = ["atom", "cid", "clashmag", "dist"]

    def __parse(self) -> None:
        """"""
        self.__processGlobalValues()
        #
        self.__processChemcalShiftList()
        #
        items = ["model", "ent", "chain", "resname", "resnum", "icode"]  # , 'ligand_geometry_outlier', 'ligand_density_outlier' ]
        #
        for node in self.__doc.getElementsByTagName("ModelledSubgroup"):
            if node.nodeType != node.ELEMENT_NODE:
                continue
            #
            residueInfo: Dict[str, str] = {}
            if node.hasAttribute("rama"):
                val = node.getAttribute("rama").strip()
                if val == "OUTLIER":
                    if not residueInfo:
                        residueInfo = self.__getMapInfo(node, items)
                    #
                    dirmap = self.__getMapInfo(node, self.__outlierMap["torsion-outlier"])
                    outlier = residueInfo.copy()
                    outlier.update(dirmap)
                    if "torsion-outlier" in self.__outlierResult:
                        self.__outlierResult["torsion-outlier"].append(outlier)
                    else:
                        listout = []
                        listout.append(outlier)
                        self.__outlierResult["torsion-outlier"] = listout
                    #
                #
            #
            if node.hasAttribute("rsrz"):
                val = node.getAttribute("rsrz").strip()
                if float(val) > 5:
                    if not residueInfo:
                        residueInfo = self.__getMapInfo(node, items)
                    #
                    outlier = residueInfo.copy()
                    outlier["rsrz"] = val
                    if "polymer-rsrz-outlier" in self.__outlierResult:
                        self.__outlierResult["polymer-rsrz-outlier"].append(outlier)
                    else:
                        listout = []
                        listout.append(outlier)
                        self.__outlierResult["polymer-rsrz-outlier"] = listout
                    #
                #
            #
            if node.hasAttribute("ligRSRZ"):
                val = node.getAttribute("ligRSRZ").strip()
                if float(val) > 5:
                    if not residueInfo:
                        residueInfo = self.__getMapInfo(node, items)
                    #
                    outlier = residueInfo.copy()
                    outlier["ligRSRZ"] = val
                    if "ligand-rsrz-outlier" in self.__outlierResult:
                        self.__outlierResult["ligand-rsrz-outlier"].append(outlier)
                    else:
                        listout = []
                        listout.append(outlier)
                        self.__outlierResult["ligand-rsrz-outlier"] = listout
                    #
                #
            #

            for childnode in node.childNodes:
                if childnode.nodeType != node.ELEMENT_NODE:
                    continue
                #
                if childnode.tagName not in self.__outlierMap:
                    continue
                #
                if not residueInfo:
                    residueInfo = self.__getMapInfo(node, items)
                #
                dirmap = self.__getMapInfo(childnode, self.__outlierMap[childnode.tagName])
                # jmb - removed cut off in reporting outliers in standard bond lengths and bond angles. Uses validation XML cut off instead.
                # if childnode.tagName == 'bond-outlier' or childnode.tagName == 'angle-outlier':
                #    if abs(float(dirmap['z'])) <= 10:
                #        continue
                #
                # skip bonds between standard residues in reporting,
                # these are better captured in pdbx_validate_polymer_linkage
                # - the validation is limited to a maxiumum distance
                # of 1.999 Angstroms in the validation report for unusual bonds
                if childnode.tagName == "bond-outlier":
                    if dirmap["atom0"] in ("C", "O3'") and dirmap["atom1"] in ("N", "P"):
                        continue

                if childnode.tagName == "mog-angle-outlier" or childnode.tagName == "mog-bond-outlier":
                    if abs(float(dirmap["Zscore"])) <= 10:
                        continue
                    #
                #
                if childnode.tagName == "clash":
                    atom_dict = {
                        "dist": dirmap["dist"],
                        "atom": dirmap["atom"],
                        "clashmag": dirmap["clashmag"],
                        "chain": node.getAttribute("chain").strip(),
                        "model": node.getAttribute("model").strip(),
                        "altcode": node.getAttribute("altcode").strip(),
                        "resnum": node.getAttribute("resnum").strip(),
                        "resname": node.getAttribute("resname").strip(),
                    }
                    if float(dirmap["dist"]) < 2.2:
                        self.clashMap.setdefault(dirmap["cid"], []).append(atom_dict)

                outlier = residueInfo.copy()
                outlier.update(dirmap)
                if childnode.tagName in self.__outlierResult:
                    cast("list[dict[str, str]]", self.__outlierResult[cast("ValidateXmlOutliersKeys", childnode.tagName)]).append(outlier)
                else:
                    listout = []
                    listout.append(outlier)
                    self.__outlierResult[cast("ValidateXmlOutliersKeys", childnode.tagName)] = listout
                #
            #
        #

        for node in self.__doc.getElementsByTagName("ModelledEntityInstance"):
            if node.nodeType != node.ELEMENT_NODE:
                continue

            if node.hasAttribute("average_residue_inclusion"):
                try:
                    if float(node.getAttribute("average_residue_inclusion").strip()) < 0.1:
                        if "chain_average_residue_inclusion" not in self.__outlierResult:
                            self.__outlierResult["chain_average_residue_inclusion"] = []
                        self.__outlierResult["chain_average_residue_inclusion"].append(
                            {
                                "chain": node.getAttribute("chain").strip(),
                                "model": node.getAttribute("model").strip(),
                                "average_residue_inclusion": float(node.getAttribute("average_residue_inclusion").strip()) * 100,
                            }
                        )
                except ValueError:
                    pass

        if self.clashMap:
            for o in self.clashMap:
                # check that there are two clashes
                if len(self.clashMap[o]) > 1:
                    clashitem = {
                        "res1model": self.clashMap[o][0]["model"],
                        "res1num": self.clashMap[o][0]["resnum"],
                        "res1name": self.clashMap[o][0]["resname"],
                        "res1chain": self.clashMap[o][0]["chain"],
                        "res1alt": self.clashMap[o][0]["altcode"],
                        "res1atom": self.clashMap[o][0]["atom"],
                        "res2model": self.clashMap[o][1]["model"],
                        "res2num": self.clashMap[o][1]["resnum"],
                        "res2chain": self.clashMap[o][1]["chain"],
                        "res2alt": self.clashMap[o][1]["altcode"],
                        "res2name": self.clashMap[o][1]["resname"],
                        "res2atom": self.clashMap[o][1]["atom"],
                        "dist": self.clashMap[o][0]["dist"],
                        "clashmag": self.clashMap[o][0]["clashmag"],
                    }
                    #
                    if clashitem["res1atom"][0] != "H" and clashitem["res2atom"][0] != "H":
                        self.clashOutliers.append(clashitem)
                    #
                #
            #
        #

    def __getSummaryValues(self) -> None:
        summaryList = [
            "DCC_Rfree",
            "clashscore",
            "percent-RSRZ-outliers",
            "percent-rama-outliers",
            "atom_inclusion_all_atoms",
            "atom_inclusion_backbone",
            "contour_level_primary_map",
        ]

        Entry = self.__doc.getElementsByTagName("Entry")[0]
        for item in summaryList:
            if Entry.getAttribute(item) and Entry.getAttribute(item) != "NotAvailable":
                try:  # noqa: SIM105
                    self.summaryValues[item] = float(Entry.getAttribute(item))
                except:  # noqa: E722 pylint: disable=bare-except
                    pass

    def __processGlobalValues(self) -> None:
        """"""
        self.__getSummaryValues()
        global_values = {}
        Entry = self.__doc.getElementsByTagName("Entry")[0]
        for item in ("DCC_Rfree", "PDB-Rfree", "DCC_R", "PDB-R"):
            if Entry.getAttribute(item) and Entry.getAttribute(item) != "NotAvailable":
                global_values[item] = Entry.getAttribute(item)
            #
        for item2 in ("atom_inclusion_all_atoms", "atom_inclusion_backbone"):
            if Entry.getAttribute(item2) and Entry.getAttribute(item2) != "NotAvailable":
                value = Entry.getAttribute(item2)
                if float(value) < 0.4:
                    self.__outlierResult[item2] = value
        #
        if Entry.getAttribute("DataCompleteness") and Entry.getAttribute("DataCompleteness") != "NotAvailable":
            self.__calculated_completeness = Entry.getAttribute("DataCompleteness")
        #
        for global_list in (("r_free_diff", "DCC_Rfree", "PDB-Rfree"), ("r_work_diff", "DCC_R", "PDB-R")):
            if (global_list[1] in global_values) and (global_list[2] in global_values):
                if abs(float(global_values[global_list[1]]) - float(global_values[global_list[2]])) > 0.05:
                    r_map = {}
                    r_map["diff"] = str(abs(float(global_values[global_list[1]]) - float(global_values[global_list[2]])))
                    r_map[global_list[1]] = global_values[global_list[1]]
                    r_map[global_list[2]] = global_values[global_list[2]]
                    self.__outlierResult[global_list[0]] = [r_map]
                #
            #
        #

    def __processChemcalShiftList(self) -> None:
        """ chemical_shift_list.attributes = ( 'block_name', 'file_id', 'file_name', 'list_id', 'number_of_errors_while_mapping', 'number_of_mapped_shifts' \
                        'number_of_parsed_shifts', 'number_of_unparsed_shifts', 'number_of_warnings_while_mapping', 'total_number_of_shifts' )

            unmapped_chemical_shift.attributes = ( 'ambiguity', 'atom', 'chain', 'diagnostic', 'error', 'rescode', 'resnum', 'value' )

            chemical_shift_outlier.attributes = ( 'atom', 'chain', 'method', 'prediction', 'rescode', 'resnum', 'value', 'zscore' )

            referencing_offset.attributes = ( 'atom', 'number_of_measurements', 'precision', 'uncertainty', 'value' )
        """
        csList = self.__doc.getElementsByTagName("chemical_shift_list")
        if len(csList) < 1:
            return
        #
        for csNode in csList:
            if csNode.getAttribute("number_of_errors_while_mapping"):
                self.__number_of_errors_while_mapping += int(csNode.getAttribute("number_of_errors_while_mapping"))
            #
            if csNode.getAttribute("number_of_warnings_while_mapping"):
                self.__number_of_warnings_while_mapping += int(csNode.getAttribute("number_of_warnings_while_mapping"))
            #
            unmappedCsList = csNode.getElementsByTagName("unmapped_chemical_shift")
            if len(unmappedCsList) > 0:
                for unmappedNode in unmappedCsList:
                    notMappedCsResidueFlag = False
                    if unmappedNode.getAttribute("diagnostic").startswith("Residue not found in structure."):
                        notMappedCsResidueFlag = True
                    #
                    csData = []
                    for attribute in ("chain", "resnum", "rescode", "atom", "value", "error", "ambiguity"):
                        if unmappedNode.getAttribute(attribute):
                            csData.append(unmappedNode.getAttribute(attribute))
                        else:
                            csData.append("")
                        #
                    #
                    self.__not_found_in_structure_cs_list.append(csData)
                    if notMappedCsResidueFlag:
                        self.__not_found_residue_in_structure_cs_list.append(csData)
                    #
                #
            #
            csOutlierList = csNode.getElementsByTagName("chemical_shift_outlier")
            if len(csOutlierList) > 0:
                for outlierNode in csOutlierList:
                    csData = []
                    for attribute in ("chain", "resnum", "rescode", "atom", "value", "prediction", "zscore"):
                        if outlierNode.getAttribute(attribute):
                            csData.append(outlierNode.getAttribute(attribute))
                        else:
                            csData.append("")
                        #
                    #
                    self.__cs_outlier_list.append(csData)
                #
            #
            offsetList = csNode.getElementsByTagName("referencing_offset")
            if len(offsetList) > 0:
                for offsetNode in offsetList:
                    csData = []
                    for attribute in ("atom", "number_of_measurements", "precision", "uncertainty", "value"):
                        if offsetNode.getAttribute(attribute):
                            csData.append(offsetNode.getAttribute(attribute))
                        else:
                            csData.append("")
                        #
                    #
                    if csData[2] and csData[3] and csData[4]:
                        # precision = float(csData[2])
                        uncertainty = float(csData[3])
                        value = float(csData[4])
                        # if (value - precision) < uncertainty:
                        # for D_8000210797
                        if abs(value) < uncertainty:
                            continue
                        #
                        self.__has_cs_referencing_offset_flag = True
                    #
                    self.__cs_referencing_offset_list.append(csData)
                #
            #
        #

    def __getMapInfo(self, node: minidom.Element, items: list[str]) -> dict[str, str]:
        """"""
        mapping: dict[str, str] = {}
        for item in items:
            val = ""
            if node.hasAttribute(item):
                val = node.getAttribute(item).strip()
            #
            mapping[item] = val
        #
        return mapping


if __name__ == "__main__":  # pragma: no cover
    try:
        obj = ValidateXml(FileName=sys.argv[1])
        summary = obj.getSummary()
        print(summary)
        #       list = obj.getOutlier('polymer-rsrz-outlier')
        #       print(list)
        list1 = obj.getOutlier("r_free_diff")
        print(list1)
        ret = obj.getOutlier("atom_inclusion_all_atoms")
        print(ret)
        #       print(obj.getClashOutliers())
        print(obj.getCsMappingErrorNumber())
        print(obj.getCsMappingWarningNumber())
        print(len(obj.getNotFoundInStructureCsList()))
        print(len(obj.getCsOutliers()))
        print(obj.getCsReferencingOffsetFlag())
    except:  # noqa: E722 pylint: disable=bare-except
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
