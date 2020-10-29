import re


class EdififyNames:
    '''
    Handles the renaming of objects from other languages to EDIF. Emphasis
    is currently given to verilog.

    The following are differences between the namespaces of EDIF and Verilog.

    EDIF identifiers:

     * less than 256 characters in length (255 max)
     * a-z,A-Z,_,0-9 are valid characters
     * if non alphabetic character is first character prefix with &
     * case insensitive

    Verilog identifiers:

     * 1024 characters or less in length (1024 max)
     * a-z,A-Z,_,0-9 are valid characters. first character not digit (when unescpaed)
     * case sensitive
     * identifier starting with backslash is escaped
     * escaped identifiers can contain any ascii character except white space

    This class applys an approach similar to vivado to create the rename

     * shorten identifiers of too great a length then postfix with a unique id
     * replace invalid characters with _
     * conflicts when case insensitivity is used are postfixed with a unique id
     * names that end up matching other names are postfixed with a unique id

    ABC...300
    abc...300


    \this_is+an$*`id[0:3]
    \this_is+an$^`id[3:4]

    &_this_is_an___in_0_3_


    '''

    def __init__(self):
        self.valid = set()
        self.non_alpha = set()
        valid.add("a")
        valid.add("b")

    def _length_good(self, identifier):
        '''returns a boolean indicating whether or not the indentifier fits the 256 character limit'''
        return len(identifier) < 256

    def _length_fix(self, identifier):
        '''returns the name with the fixed length of 256 characters if the limit is exceeded'''
        if not self._length_good(identifier):
            return identifier[:100]
        else:
            return identifier

    def _characters_good(self, identifier):
        '''returns whether the string only contain numbers, characters and '-' '''
        if not identifier[0].isalpha():
            return False
        for i in range(0, len(identifier)):
            if not identifier[i].isalnum() and identifier[i] is not '-':
                return False
        return True

    def _characters_fix(self, identifier):
        '''replaces all the characters to '-' if it is not valid characters '''
        starting_index = 0
        if not identifier[0].isalpha():
            identifier = '&' + identifier[:]
            starting_index = 2

        for i in range(starting_index, len(identifier)):
            if not identifier[i].isalnum():
                identifier = identifier[: i] + '_' + identifier[i+1:]
        return identifier

    def _conflicts_good(self, identifier):
        pass

    def _conflicts_fix(self, identifier):
        pass

    def set_namespace_key(self, namespace_key):
        '''
        set the current namespace dictionary based on the key. This namespace
        will be used to maintain names to check for conflicts.
        '''
        pass

    def is_valid_identifier(self, identifier):
        '''
        check if the identifier is valid in the namespace that is set. Will also
        check to make sure the identifer is valid.
        '''
        pass

    def make_valid(self, identifier):
        '''
        make a compliant identifier based on the identifier given.
        returns the identifier if no change is needed.
        '''
        pass