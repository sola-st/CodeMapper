import argparse
from anything_tracker.CandidateRegion import show_candidate_region
from anything_tracker.ComputeCandidateRegions import ComputeCandidateRegions


parser = argparse.ArgumentParser(description="Track anything you want between two different versions.")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--base_commit", help="the commit to get the 1st version of the target file", required=True)
parser.add_argument("--target_commit", help="the commit to get the 2nd version of the target file", required=True)
parser.add_argument("--file_path", help="the target file that you want to track", required=True)
parser.add_argument("--interest_element_character_range", help="a 4-element list, to show where to track", required=True)


def character_range_to_line_range(interest_element_character_range):
    '''   
    interest_element_character_range: 
        start_line, 
        start_character_index, 
        end_line, 
        end_character_index
    all start at 1.
    '''
    interest_line_range = ""
    interest_start_line = interest_element_character_range[0]
    interest_end_line = interest_element_character_range[2]
    interest_line_range = range(interest_start_line, interest_end_line+1)
    return interest_line_range

def main(repo_dir, base_commit, target_commit, file_path, interest_line_range):
    ''' 
    Step 1: Get all candidate candidates
     * 1.1 git diff changed hunks
     * 1.2 exactly mapped lines
     * 1.3 ...
    '''
    init = ComputeCandidateRegions(repo_dir, base_commit, target_commit, file_path, interest_line_range)
    candidate_regions = init.run()

    for candidate in candidate_regions:
        show_candidate_region(candidate)

    # TODO Other steps


if __name__ == "__main__":
    # args = parser.parse_args()
    # interest_line_range = character_range_to_line_range(args.interest_element_character_range)
    # main(args.repo_dir, args.base_commit, args.target_commit, args.file_path, interest_line_range)

    # one-click test, 
    '''
    Test 1: https://github.com/rails/rails/commit/2edcda85764d369d4f46b034f0e9694f63e93e30
    Expected candidate 4 regions:
     * 2 exactly the same with specified line 13. --> lines 13 and 24.
     * 2 ignore the whitespace before the line. (1 from unchanged lines, another one from diff hunk) --> lines 39, 52(added line)
    '''
    repo_dir = "data/repos/rails"
    # test 1, single-line source region and continuous multi-line source region
    # base_commit = "550c5d2"
    # target_commit = "2edcda8"
    # file_path = "activestorage/test/jobs/transform_job_test.rb"
    # # interest_line_range = range(46, 47) # start at 1, the candidates include a diff hunk
    # # interest_line_range = range(13, 15)
    # interest_line_range = range(13, 14)
    # interest_line_range = range(interest_line_range.start - 1 , interest_line_range.stop - 1)
    # main(repo_dir, base_commit, target_commit, file_path, interest_line_range)

    # test 2, discontinuous multi-line source region
    # https://github.com/rails/rails/commit/8ec3843cd8253e0ea92839d5c3a6a68a7a39e297
    base_commit = "01492e3"
    target_commit = "8ec3843"
    file_path = "activemodel/lib/active_model/attribute_methods.rb"
    # interest_line_range = range(229, 232) # 230 is an empty line
    interest_line_range = range(235, 238) # involved in changed hunk
    interest_line_range = range(interest_line_range.start - 1 , interest_line_range.stop - 1)
    main(repo_dir, base_commit, target_commit, file_path, interest_line_range)
    # print("Done.")