# safeCodeProvider
A project that provides an environment for solving exams and assignments without using LLMs.








```cd safeCodeProvider```

```docker build -t safe-code-provider .```
linux or macos 
```ifconfig```

windows 
```ipconfig```

get local ip by using above commands

and run the following command by replacing YOUR_LOCAL_IP with your local ip

```docker run -p 8000:8000 -p 8001:8001 --name safe-code-container -e LOCAL_IP=YOUR_LOCAL_IP safe-code-provider```

