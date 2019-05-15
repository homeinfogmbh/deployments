FILE_LIST = ./.installed_files.txt

.PHONY: pull push clean install uninstall dom

default: | pull clean dom install

install:
	@ ./setup.py install --record $(FILE_LIST)

uninstall:
	@ while read FILE; do echo "Removing: $$FILE"; rm "$$FILE"; done < $(FILE_LIST)

clean:
	@ rm -Rf ./build

pull:
	@ git pull

push:
	@ git push

dom:
	@ pyxbgen -u files/tenant2tenant.xsd -m dom --module-prefix=tenant2tenant
