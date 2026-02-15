Use a principal engineer lens like Jeff dean and Martin Fowler to plan and execute the refactoring

Look at @/libs and @/bin/sor to see what can be 
1. Cleaned up
2. Unused or duplicate function that can be removed
3. Unused or unneeded comments that can be removed
4. Low hanging optimisations that can be done
5. Reducing code smell by having simple deep abstractions 
6. Unnecessary test to be removed
7. Test that should be added.

After analysing the code come up with a. Plan for the refaforring. Create a new branch for each of the large refactoring. Commit incrementally and then make a pr for each of the refactor. 