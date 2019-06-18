// Copyright (c) Microsoft Corporation.
// Sample test driver demonstrating in-place fuzzing
// feature of Microsoft Security Risk Detection service.
// In-place fuzzing feature allows seeds refer to other files
// with different file extensions.

#include <iostream>
#include <stdio.h>
#include <string.h>

// File header definition
struct Header {
    char* constant;
    char* searchString;
    int numberOfReferenceFiles;
};

// File format definition
struct FileFormat {
    Header header;
    char** files;
};

char* loadFile(char* filePath) {
    if (filePath == NULL) {
        return NULL;
    }
    FILE* pSeed = fopen(filePath, "rb");
    if (pSeed == NULL) {
        return NULL;
    }

    fseek(pSeed, 0, SEEK_END);
    size_t size = ftell(pSeed);
    rewind(pSeed);

    char* buffer = (char*)malloc(sizeof(char) * (size + 1UL));
    if (buffer == NULL) {
        free(buffer);
        return NULL;
    }
    memset(buffer, NULL, sizeof(char) * (size + 1UL));
    size_t bytesRead = fread(buffer, sizeof(char), size, pSeed);
    fclose(pSeed);

    if (0 == bytesRead) {
        free(buffer);
        return NULL;
    }
    return buffer;
}

// Load file from the specified path
// Do not check for any errors
FileFormat parseFile(char* filePath) {
    char* buffer = loadFile(filePath);
    Header header = { NULL, NULL, -1 };

    char* pch = strtok(buffer, "\n");
    while (pch != NULL)
    {
        size_t len = strlen(pch);

        if (header.constant == NULL) {
            header.constant = _strdup(pch);
        }
        else if (header.searchString == NULL) {
            header.searchString = _strdup(pch);
        }
        else {
            header.numberOfReferenceFiles = atoi(pch);
            break;
        }
        pch = strtok(NULL, "\n");
    }

    FileFormat fileFormat = { header, (char**)malloc(sizeof(char*) * header.numberOfReferenceFiles) };

    if (header.numberOfReferenceFiles <= 0) {
        free(fileFormat.files);
        fileFormat.files = NULL;
        return fileFormat;
    }

    for (int i = 0; i < header.numberOfReferenceFiles; i++) {
        pch = strtok(NULL, "\n");
        fileFormat.files[i] = _strdup(pch);
    }
    free(buffer);
    return fileFormat;
}

int searchForStringInBuffer(char* buffer, char* searchString) {
    if (buffer == NULL || searchString == NULL) {
        return 0;
    }

    int occurences = 0;
    char* found = strstr(buffer, searchString);
    size_t searchLen = strlen(searchString);
    while (found != NULL) {
        occurences++;
        found = strstr(found + searchLen, searchString);
    }
    return occurences;
}

int searchForString(char* files[], int nFiles, char* searchString) {
    if (nFiles <= 0 || searchString == NULL || files == NULL) {
        return 0;
    }

    int totalOccurences = 0;

    for (int i = 0; i < nFiles; i++) {
        char* buffer = loadFile(files[i]);
        totalOccurences += searchForStringInBuffer(buffer, searchString);
        free(buffer);
    }
    return totalOccurences;
}

int main(int argc, char* argv[])
{
    if (argc != 2) {
        printf("Expected path to a file as an argument");
        return -1;
    }
    char* seedFilePath = argv[1];
    FileFormat mainSeed = parseFile(seedFilePath);

    int occurrences = searchForString(mainSeed.files, mainSeed.header.numberOfReferenceFiles, mainSeed.header.searchString);
    printf("Found %d number of occurences of the string %s", occurrences, mainSeed.header.searchString);

    if (0 == strcmp(mainSeed.header.searchString, "POLO") && occurrences > 0) {
        char buffer[1];
        printf("Forcing buffer overflow");
#pragma prefast(suppress:__WARNING_POTENTIAL_BUFFER_OVERFLOW_HIGH_PRIORITY,"this is an example bug in program")
        strcpy(buffer, mainSeed.header.searchString);
    }

    free(mainSeed.header.constant);
    free(mainSeed.header.searchString);
    free(mainSeed.files);

    return 0;
}
