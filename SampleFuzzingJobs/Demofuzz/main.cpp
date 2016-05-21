#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>

int __cdecl main(int argc, __in_ecount(argc) char** argv) 
{
    int iRet;
    HANDLE hFile;
    PCSTR pcszFileName;

    if (argc <= 1)
    {
        printf("USAGE: %S <filename>\n",argv[0]);
        return 0;
    }

    iRet = 1;
    pcszFileName = argv[1];
    hFile = CreateFile(pcszFileName,
                       GENERIC_READ, 
                       FILE_SHARE_READ, 
                       NULL, 
                       OPEN_EXISTING, 
                       FILE_ATTRIBUTE_NORMAL, 
                       NULL);

    if (hFile != INVALID_HANDLE_VALUE) 
    {
        DWORD dwFileSize;
        const DWORD c_dwMinFileSize = 2;

        dwFileSize = GetFileSize(hFile, 0);
        if (dwFileSize >= c_dwMinFileSize)
        {
            PBYTE pbBuffer;

            pbBuffer = new BYTE[c_dwMinFileSize];
            if (pbBuffer)
            {
                DWORD cbRead;

                if (ReadFile(hFile, pbBuffer, c_dwMinFileSize, &cbRead, NULL)) 
                {
                    if (0 == pbBuffer[0])
                    {
                        PINT piMalloc;

                        printf("Writing data to the heap\n");
                        piMalloc = (PINT)(malloc(argc * sizeof(int)));
                        piMalloc[pbBuffer[1]] = 0;
                        free(piMalloc);
                    }
                    else
                    {
                        PINT piAllocA;

                        printf("Writing data to the stack\n");
                        piAllocA = &iRet;
                        #pragma prefast(suppress:__WARNING_POTENTIAL_BUFFER_OVERFLOW_HIGH_PRIORITY,"this is an example bug in program")
                        piAllocA[pbBuffer[1]] = 0;
                    }

                    iRet = 0;
                }
                else
                {
                    printf("ReadFile(%s) because of error %u\n", pcszFileName, GetLastError());
                }

                delete [] pbBuffer;
            }
            else
            {
                printf("Out of memory\n");
            }
        }
        else
        {
            printf("File %s has size %u bytes; expected size to be at least 2 bytes\n", pcszFileName, dwFileSize);
        }
        
        CloseHandle(hFile);
    }
    else
    {
        printf ("ERROR: unable to open file %s\n", pcszFileName);
    }
  
    return iRet;  
}
