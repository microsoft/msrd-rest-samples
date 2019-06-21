// Copyright (c) Microsoft Corporation.
// Sample test driver demonstrating in-place fuzzing
// feature of Microsoft Security Risk Detection service.
// In-place fuzzing feature allows seeds refer to other files
// with different file extensions.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <direct.h>

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
        printf("Failed to read file `%s`\n", filePath);
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
// Minimal error checking - enough to not crash/hang loading the file,
// but other errors (like too few fields) are ignored.
FileFormat parseFile(char* filePath) {
    char* buffer = loadFile(filePath);

    Header header = { NULL, NULL, -1 };

    if (buffer == NULL) {
        FileFormat fileFormat = { header, NULL };
        return fileFormat;
    }

    char* pch = strtok(buffer, ",");
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
            if (header.numberOfReferenceFiles > 10) {
                // Set a limit to avoid hangs allocating large arrays when fuzzing.
                header.numberOfReferenceFiles = 10;
            }
            break;
        }
        pch = strtok(NULL, ",");
    }

    FileFormat fileFormat = { header, (char**)malloc(sizeof(char*) * header.numberOfReferenceFiles) };

    if (header.numberOfReferenceFiles <= 0) {
        free(fileFormat.files);
        fileFormat.files = NULL;
        return fileFormat;
    }

    for (int i = 0; i < header.numberOfReferenceFiles; i++) {
        pch = strtok(NULL, ",");
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

    int totalOccurrences = 0;

    for (int i = 0; i < nFiles; i++) {
        printf("searching file `%s`\n", files[i]);
        char* buffer = loadFile(files[i]);
        totalOccurrences += searchForStringInBuffer(buffer, searchString);
        free(buffer);
    }

    if (0 == strcmp(searchString, "YOLO") && totalOccurrences > 0) {
        char buffer[1];
        printf("Forcing buffer overflow");
#pragma prefast(suppress:__WARNING_POTENTIAL_BUFFER_OVERFLOW_HIGH_PRIORITY,"this is an example bug in program")
        strcpy(buffer, searchString);
    }

    return totalOccurrences;
}

int main(int argc, char* argv[])
{
    if (argc != 2) {
        printf("Expected path to a file as an argument");
        return -1;
    }
    char* seedFilePath = argv[1];
    FileFormat mainSeed = parseFile(seedFilePath);

    char dir[_MAX_DIR];
    _splitpath(seedFilePath, NULL, dir, NULL, NULL);
    _chdir(dir);

    int occurrences = searchForString(mainSeed.files, mainSeed.header.numberOfReferenceFiles, mainSeed.header.searchString);
    printf("Found %d number of occurrences of the string %s\n", occurrences, mainSeed.header.searchString);

    free(mainSeed.header.constant);
    free(mainSeed.header.searchString);
    for (int i = 0; i < mainSeed.header.numberOfReferenceFiles; i++) {
        free(mainSeed.files[i]);
    }
    free(mainSeed.files);

    return 0;
}
