file = open('C:\\Users\\arbaz\\OneDrive\\Desktop\\codedex\\filer.txt','w')
arr = ['get an intership',' get a job', 'get married', 'move to canda']
file.write('Things to do')
i=1
for a in arr:
    print(str(i)+" "+ a +"\n")
    file.write(f'{i}.{a}\n')
    i+=1
file.close()

