# coding: utf-8

class Template:
    #-----------------------------------------------------------------------------------------------
    #
    #   Get and return nftables template
    #
    #-----------------------------------------------------------------------------------------------
    def get(self):
        #
        # Read the template file
        #
        try:
            f = open('/opt/ezfirewall/templates/netfilter.conf.template', 'r')
            content = f.read()
            f.close()

            return content
        except Exception as e:
            raise Exception('could not read the template file /opt/ezfirewall/templates/netfilter.conf.template: ' + str(e))
        
