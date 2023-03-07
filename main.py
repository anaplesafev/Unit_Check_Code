import shutil
import sys
import xml.etree.ElementTree as ET
import os
import stat
from zipfile import ZipFile
import logging

#my_dict = {}
log = logging.getLogger('root')

#function used to do SVN Checkout. It receives as an argument the path from SVN that we need to find the first input file
def SVN_checkout(SVN_URL):
    try:
        os.system('svn co ' + SVN_URL + ' SVN')
        absolute_path = 'SVN\\Autosar\\BMW_Units.arxml'
        return absolute_path
    except:
        sys.exit(1)

#function used to generate the new input file. Takes as argument the path from the artifactory
def Generate_new_file(path_to_artifactory, build_version):
    try:
        SVN_URL = 'https://asc-repoa.bmwgroup.net/svn/asc186/Projects/BMW.EA.Build/tags/'+build_version
        print SVN_URL
        os.system('svn co ' + SVN_URL + ' E:\\tools\\EaBuild\\'+build_version)

        os.system(r'e:\tools\EaBuild\\'+build_version+'\\build.bat --configuration_validate=false --bundle=sw@tpl@masterdata --references='+path_to_artifactory  +' masterdata')
        path_to_new_file= '.build\\masterdata\\MasterData\\BMW_Units.arxml'
        print(os.path.dirname(__file__))
        return path_to_new_file
    except:
        sys.exit(1)

#the function that creates the archive with the two input files. Takes the input files as arguments
def CreateZip(file1, file2):
    zipObj = ZipFile('input_files.zip', 'w')
    # Add multiple files to the zip
    zipObj.write(file1)
    zipObj.write(file2)
    # close the Zip File
    zipObj.close()

#function that helps to go through the documents up to the units themselves. Receives the file as a parameter
def getAllElements(file):
    tree = ET.parse(file)
    XML_NAMESPACE = "http://autosar.org/schema/r4.0"
    path_to_elements= ('./{http://autosar.org/schema/r4.0}AR-PACKAGES/' +
                         '{http://autosar.org/schema/r4.0}AR-PACKAGE/'  +
                         '{http://autosar.org/schema/r4.0}AR-PACKAGES/' +
                         '{http://autosar.org/schema/r4.0}AR-PACKAGE/'  +
                         '{http://autosar.org/schema/r4.0}AR-PACKAGES/' +
                         '{http://autosar.org/schema/r4.0}AR-PACKAGE/'  +
                         '{http://autosar.org/schema/r4.0}ELEMENTS/*')
    elements = tree.findall(path_to_elements)
    return getUnitsData(elements, path_to_elements, tree)

#function that extracts the units. is called inside the "getAllElements" function
def getUnitsData(elements, path_to_elements, tree):
    xml_namespace= '{http://autosar.org/schema/r4.0}'
    unit_xpath= path_to_elements[:-1] + '{http://autosar.org/schema/r4.0}UNIT/*'
    unit_children = tree.findall(unit_xpath)
    units = []
    new_unit = {}
    found_short_name = False
    unit_name = unit_children[0].tag.replace(xml_namespace, "")
    new_unit[unit_name] = unit_children[0].text
    for unit_child in unit_children[1:]:
        found_short_name = False
        if unit_child.tag.endswith("SHORT-NAME"):
            found_short_name = True
            units.append(new_unit)
            new_unit = {}
        unit_name = unit_child.tag.replace(xml_namespace,"")
        new_unit[unit_name] = unit_child.text
    units.append(new_unit)
    #for unit in units:
    #    print unit
    return units

#function that returns the differences between the two lists of units. Takes the lists as arguments
def get_difference(list_a, list_b):
    li_dif = [i for i in list_a + list_b if i not in list_a or i not in list_b]
    #print list_a
    return li_dif

#function used to delete the SVN tags from the file where the SVN Checkout is done
def del_evenReadonly(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)

#main contains the logic of the script. it uses the repository path and the artifactory path to automatically generate the input files that it parses into units and creates a .txt file with the differences between them.
#after running, the input and additional files are deleted and an archive is created with only the two input files.
if __name__ == "__main__":
    repository_path = 'https://asc-repo.bmwgroup.net/svn/asc045/Shared/BMW_SHD_S68T0_Proj.SP21/trunk'  # aici adaug calea catre SVN a project shared-ului
    artifactory_path = 'https://powertrain.artifactory.cc.bmwgroup.net/artifactory/powertrain-production-local/de.bmw.powertrain.shareds/BMW_SHD_S68T0_DME2_Arch/default/stable/SP21/048.01/0-zqfnrshmo62wjtp2f3gjhgmeq4' #calea catre art pentru artitechture shared
    build_version= '048.01.1'
    # build_version = '048.00.2'
    old_file = SVN_checkout(repository_path)
    new_file = Generate_new_file(artifactory_path, build_version)
    SVN_checkout(repository_path)
    Generate_new_file(artifactory_path, build_version)
    CreateZip(old_file, new_file)
    var1 = getAllElements(old_file)
    var2 = getAllElements(new_file)
    print "\n"
    #print var1

    li3 = get_difference(var1, var2)
    print(li3)
    with open(r'diffs.txt', 'w') as fp:
        for item in li3:
            # write each item on a new line
            fp.write("%s\n" % item)
        print('Done')

    shutil.rmtree('.build')
    root = 'SVN'
    for root, subFolders, files in os.walk(os.getcwd()):
        if '.svn' in subFolders:
            shutil.rmtree(root + '\.svn', onerror=del_evenReadonly)
    shutil.rmtree('SVN')